"""Training script for detector."""
import argparse
import copy
import os
from datetime import datetime
from typing import Tuple, Optional, Callable
import random
import matplotlib.pyplot as plt
import torch
import wandb
from PIL import Image
from pycocotools.cocoeval import COCOeval
from torch import nn
from torchvision.datasets import CocoDetection
import utils
from detector import Detector
from functools import partial

NUM_CATEGORIES = 8
VALIDATION_ITERATION = 100
NUM_ITERATIONS = 20000
LEARNING_RATE = 1e-4
WEIGHT_POS = 1
WEIGHT_NEG = 1
WEIGHT_REG = 1
WEIGHT_CLASS = 10
BATCH_SIZE = 8
N_TEST_IMAGES = 30


def compute_loss(
    prediction_batch: torch.Tensor, target_batch: torch.Tensor
) -> Tuple[torch.Tensor]:
    """Compute loss between predicted tensor and target tensor.

    Args:
        prediction_batch: Batched predictions. Shape (N,C,H,W).
        target_batch: Batched targets. shape (N,C,H,W).

    Returns:
        Tuple of three separate loss terms:
            reg_mse: Mean squared error of regression targets.
            pos_mse: Mean squared error of positive confidence channel.
            neg_mse: Mean squared error of negative confidence channel.
    """
    # positive / negative indices
    # (this could be passed from input_transform to avoid recomputation)
    pos_indices = torch.nonzero(target_batch[:, 4, :, :] == 1, as_tuple=True)
    neg_indices = torch.nonzero(target_batch[:, 4, :, :] == 0, as_tuple=True)

    # compute loss
    reg_mse = nn.functional.mse_loss(
        prediction_batch[pos_indices[0], 0:4, pos_indices[1], pos_indices[2]],
        target_batch[pos_indices[0], 0:4, pos_indices[1], pos_indices[2]],
    )
    pos_mse = nn.functional.mse_loss(
        prediction_batch[pos_indices[0], 4, pos_indices[1], pos_indices[2]],
        target_batch[pos_indices[0], 4, pos_indices[1], pos_indices[2]],
    )
    neg_mse = nn.functional.mse_loss(
        prediction_batch[neg_indices[0], 4, neg_indices[1], neg_indices[2]],
        target_batch[neg_indices[0], 4, neg_indices[1], neg_indices[2]],
    )

    pred_class_vector = prediction_batch[:, 5:, :, :]
    target_class_vector = target_batch[:, 5:, :, :]
    class_loss = nn.CrossEntropyLoss()(pred_class_vector, target_class_vector)

    return reg_mse, pos_mse, neg_mse, class_loss


def train(device: str = "cpu") -> None:
    """Train the network.

    Args:
        device: The device to train on.
    """
    wandb.init(project="detector_baseline")

    # Init model
    detector = Detector().to(device)

    wandb.watch(detector)

    dataset = CocoDetection(
        root="./data/",
        annFile="./annotations/train3.json",
        transforms=partial(detector.input_transform, validation=False),
    )
    val_dataset = CocoDetection(
        root="./data/",
        annFile="./annotations/val3.json",
        transforms=partial(detector.input_transform, validation=True),
    )

    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=True
    )
    val_dataloader = torch.utils.data.DataLoader(val_dataset, batch_size=BATCH_SIZE)

    # training params
    wandb.config.max_iterations = NUM_ITERATIONS
    wandb.config.learning_rate = LEARNING_RATE
    wandb.config.weight_pos = WEIGHT_POS
    wandb.config.weight_neg = WEIGHT_NEG
    wandb.config.weight_reg = WEIGHT_REG

    # run name (to easily identify model later)
    time_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    run_name = wandb.config.run_name = "det_{}".format(time_string)

    # init optimizer
    optimizer = torch.optim.Adam(detector.parameters(), lr=LEARNING_RATE)

    # load test images
    # these will be evaluated in regular intervals
    test_images = []
    orig_test_images = []
    show_test_images = False
    directory = "./test_images"
    if not os.path.exists(directory):
        os.makedirs(directory)
    for file_name in sorted(os.listdir(directory))[:N_TEST_IMAGES]:
        if file_name.endswith(".jpeg") or file_name.endswith(".jpg"):
            file_path = os.path.join(directory, file_name)
            test_image = Image.open(file_path)
            orig_test_images.append(test_image)
            torch_image, _ = detector.input_transform(test_image, [], validation=True)
            test_images.append(torch_image)

    if test_images:
        test_images = torch.stack(test_images)
        test_images = test_images.to(device)
        show_test_images = True

    print("Training started...")

    current_iteration = 1
    while current_iteration <= NUM_ITERATIONS:
        for img_batch, target_batch in dataloader:
            img_batch = img_batch.to(device)
            target_batch = target_batch.to(device)

            # run network
            out = detector(img_batch)

            reg_mse, pos_mse, neg_mse, class_loss = compute_loss(out, target_batch)
            loss = (
                WEIGHT_POS * pos_mse
                + WEIGHT_REG * reg_mse
                + WEIGHT_NEG * neg_mse
                + WEIGHT_CLASS * class_loss
            )

            # optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            wandb.log(
                {
                    "total loss": loss.item(),
                    "loss pos": pos_mse.item(),
                    "loss neg": neg_mse.item(),
                    "loss reg": reg_mse.item(),
                    "loss class": class_loss.item(),
                },
                step=current_iteration,
            )

            print(
                "Iteration: {}, loss: {}".format(current_iteration, loss.item()),
            )

            # Validate every N iterations
            if current_iteration % VALIDATION_ITERATION == 0:
                validate(detector, val_dataloader, current_iteration, device)

            # generate visualization every N iterations
            if current_iteration % VALIDATION_ITERATION == 0 and show_test_images:
                detector.eval()
                with torch.no_grad():
                    out = detector(test_images).cpu()
                    bbs = detector.decode_output(out, 0.5, scale_bb=True)

                    for i, test_image in enumerate(orig_test_images):
                        figure, ax = plt.subplots(1)
                        plt.imshow(test_image)
                        plt.imshow(
                            out[i, 4, :, :],
                            interpolation="nearest",
                            extent=(0, 1280, 720, 0),
                            alpha=0.3,
                        )

                        # add bounding boxes
                        utils.add_bounding_boxes(ax, bbs[i], utils.CLASS_DICT)

                        wandb.log(
                            {"test_img_{i}".format(i=i): figure}, step=current_iteration
                        )
                        plt.close()
                detector.train()

            current_iteration += 1
            if current_iteration > NUM_ITERATIONS:
                break

    print("\nTraining completed (max iterations reached)")

    model_path = "{}.pt".format(run_name)
    torch.save(detector, model_path)
    wandb.save(model_path)

    print("Model weights saved at {}".format(model_path))


def validate(
    detector: Detector,
    val_dataloader: torch.utils.data.DataLoader,
    current_iteration: int,
    device: str,
) -> None:
    """Compute validation metrics and log to wandb.

    Args:
        detector: The detector module to validate.
        val_dataloader: The dataloader for the validation dataset.
        current_iteration: The current training iteration. Used for logging.
        device: The device to run validation on.
    """
    detector.eval()
    coco_pred = copy.deepcopy(val_dataloader.dataset.coco)
    coco_pred.dataset["annotations"] = []
    with torch.no_grad():
        count = (
            total_pos_mse
        ) = total_reg_mse = total_neg_mse = total_class_loss = loss = 0
        image_id = ann_id = 0
        for val_img_batch, val_target_batch in val_dataloader:
            val_img_batch = val_img_batch.to(device)
            val_target_batch = val_target_batch.to(device)
            val_out = detector(val_img_batch)
            reg_mse, pos_mse, neg_mse, class_loss = compute_loss(
                val_out, val_target_batch
            )
            total_reg_mse += reg_mse
            total_pos_mse += pos_mse
            total_neg_mse += neg_mse
            total_class_loss += class_loss
            loss += (
                WEIGHT_POS * pos_mse
                + WEIGHT_REG * reg_mse
                + WEIGHT_NEG * neg_mse
                + WEIGHT_CLASS * class_loss
            )
            imgs_bbs = detector.decode_output(val_out, topk=100)
            for img_bbs in imgs_bbs:
                for img_bb in img_bbs:
                    coco_pred.dataset["annotations"].append(
                        {
                            "id": ann_id,
                            "bbox": [
                                img_bb["x"],
                                img_bb["y"],
                                img_bb["width"],
                                img_bb["height"],
                            ],
                            "area": img_bb["width"] * img_bb["height"],
                            "category_id": img_bb[
                                "category_id"
                            ],  
                            "score": img_bb["score"],
                            "image_id": val_dataloader.dataset.ids[image_id],
                        }
                    )
                    ann_id += 1
                image_id += 1
            count += len(val_img_batch) / BATCH_SIZE
        coco_pred.createIndex()
        coco_eval = COCOeval(val_dataloader.dataset.coco, coco_pred, iouType="bbox")
        coco_eval.params.useCats = 1  # TODO replace with 1 when categories are added
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()
        wandb.log(
            {
                "total val loss": (loss / count),
                "val loss pos": (total_pos_mse / count),
                "val loss neg": (total_neg_mse / count),
                "val loss reg": (total_reg_mse / count),
                "val loss class": (total_class_loss / count),
                "val AP @IoU 0.5:0.95": coco_eval.stats[0],
                "val AP @IoU 0.5": coco_eval.stats[1],
                "val AR @IoU 0.5:0.95": coco_eval.stats[8],
            },
            step=current_iteration,
        )
        print(
            "Validation: {}, validation loss: {}".format(
                current_iteration, loss / count
            ),
        )
    detector.train()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # device = parser.add_mutually_exclusive_group(required=True)
    # device.add_argument("--cpu", dest="device", action="store_const", const="cpu")
    # device.add_argument("--gpu", dest="device", action="store_const", const="cuda")
    # args = parser.parse_args()
    # train(args.device)
    train("cuda")
