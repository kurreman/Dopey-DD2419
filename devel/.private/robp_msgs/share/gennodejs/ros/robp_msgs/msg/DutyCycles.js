// Auto-generated. Do not edit!

// (in-package robp_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let std_msgs = _finder('std_msgs');

//-----------------------------------------------------------

class DutyCycles {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.duty_cycle_left = null;
      this.duty_cycle_right = null;
    }
    else {
      if (initObj.hasOwnProperty('header')) {
        this.header = initObj.header
      }
      else {
        this.header = new std_msgs.msg.Header();
      }
      if (initObj.hasOwnProperty('duty_cycle_left')) {
        this.duty_cycle_left = initObj.duty_cycle_left
      }
      else {
        this.duty_cycle_left = 0.0;
      }
      if (initObj.hasOwnProperty('duty_cycle_right')) {
        this.duty_cycle_right = initObj.duty_cycle_right
      }
      else {
        this.duty_cycle_right = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type DutyCycles
    // Serialize message field [header]
    bufferOffset = std_msgs.msg.Header.serialize(obj.header, buffer, bufferOffset);
    // Serialize message field [duty_cycle_left]
    bufferOffset = _serializer.float64(obj.duty_cycle_left, buffer, bufferOffset);
    // Serialize message field [duty_cycle_right]
    bufferOffset = _serializer.float64(obj.duty_cycle_right, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type DutyCycles
    let len;
    let data = new DutyCycles(null);
    // Deserialize message field [header]
    data.header = std_msgs.msg.Header.deserialize(buffer, bufferOffset);
    // Deserialize message field [duty_cycle_left]
    data.duty_cycle_left = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [duty_cycle_right]
    data.duty_cycle_right = _deserializer.float64(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    return length + 16;
  }

  static datatype() {
    // Returns string type for a message object
    return 'robp_msgs/DutyCycles';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '543f5f160fe8968f328a223a093313c7';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    Header header
    
    # Value should be in [-1, 1], negative is backwards, positive forwards
    float64 duty_cycle_left
    float64 duty_cycle_right
    ================================================================================
    MSG: std_msgs/Header
    # Standard metadata for higher-level stamped data types.
    # This is generally used to communicate timestamped data 
    # in a particular coordinate frame.
    # 
    # sequence ID: consecutively increasing ID 
    uint32 seq
    #Two-integer timestamp that is expressed as:
    # * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
    # * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
    # time-handling sugar is provided by the client library
    time stamp
    #Frame this data is associated with
    string frame_id
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new DutyCycles(null);
    if (msg.header !== undefined) {
      resolved.header = std_msgs.msg.Header.Resolve(msg.header)
    }
    else {
      resolved.header = new std_msgs.msg.Header()
    }

    if (msg.duty_cycle_left !== undefined) {
      resolved.duty_cycle_left = msg.duty_cycle_left;
    }
    else {
      resolved.duty_cycle_left = 0.0
    }

    if (msg.duty_cycle_right !== undefined) {
      resolved.duty_cycle_right = msg.duty_cycle_right;
    }
    else {
      resolved.duty_cycle_right = 0.0
    }

    return resolved;
    }
};

module.exports = DutyCycles;
