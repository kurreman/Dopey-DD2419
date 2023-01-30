// Generated by gencpp from file robp_msgs/Encoders.msg
// DO NOT EDIT!


#ifndef ROBP_MSGS_MESSAGE_ENCODERS_H
#define ROBP_MSGS_MESSAGE_ENCODERS_H


#include <string>
#include <vector>
#include <memory>

#include <ros/types.h>
#include <ros/serialization.h>
#include <ros/builtin_message_traits.h>
#include <ros/message_operations.h>

#include <std_msgs/Header.h>

namespace robp_msgs
{
template <class ContainerAllocator>
struct Encoders_
{
  typedef Encoders_<ContainerAllocator> Type;

  Encoders_()
    : header()
    , encoder_left(0)
    , encoder_right(0)
    , delta_encoder_left(0)
    , delta_encoder_right(0)
    , delta_time_left(0.0)
    , delta_time_right(0.0)  {
    }
  Encoders_(const ContainerAllocator& _alloc)
    : header(_alloc)
    , encoder_left(0)
    , encoder_right(0)
    , delta_encoder_left(0)
    , delta_encoder_right(0)
    , delta_time_left(0.0)
    , delta_time_right(0.0)  {
  (void)_alloc;
    }



   typedef  ::std_msgs::Header_<ContainerAllocator>  _header_type;
  _header_type header;

   typedef int64_t _encoder_left_type;
  _encoder_left_type encoder_left;

   typedef int64_t _encoder_right_type;
  _encoder_right_type encoder_right;

   typedef int32_t _delta_encoder_left_type;
  _delta_encoder_left_type delta_encoder_left;

   typedef int32_t _delta_encoder_right_type;
  _delta_encoder_right_type delta_encoder_right;

   typedef double _delta_time_left_type;
  _delta_time_left_type delta_time_left;

   typedef double _delta_time_right_type;
  _delta_time_right_type delta_time_right;





  typedef boost::shared_ptr< ::robp_msgs::Encoders_<ContainerAllocator> > Ptr;
  typedef boost::shared_ptr< ::robp_msgs::Encoders_<ContainerAllocator> const> ConstPtr;

}; // struct Encoders_

typedef ::robp_msgs::Encoders_<std::allocator<void> > Encoders;

typedef boost::shared_ptr< ::robp_msgs::Encoders > EncodersPtr;
typedef boost::shared_ptr< ::robp_msgs::Encoders const> EncodersConstPtr;

// constants requiring out of line definition



template<typename ContainerAllocator>
std::ostream& operator<<(std::ostream& s, const ::robp_msgs::Encoders_<ContainerAllocator> & v)
{
ros::message_operations::Printer< ::robp_msgs::Encoders_<ContainerAllocator> >::stream(s, "", v);
return s;
}


template<typename ContainerAllocator1, typename ContainerAllocator2>
bool operator==(const ::robp_msgs::Encoders_<ContainerAllocator1> & lhs, const ::robp_msgs::Encoders_<ContainerAllocator2> & rhs)
{
  return lhs.header == rhs.header &&
    lhs.encoder_left == rhs.encoder_left &&
    lhs.encoder_right == rhs.encoder_right &&
    lhs.delta_encoder_left == rhs.delta_encoder_left &&
    lhs.delta_encoder_right == rhs.delta_encoder_right &&
    lhs.delta_time_left == rhs.delta_time_left &&
    lhs.delta_time_right == rhs.delta_time_right;
}

template<typename ContainerAllocator1, typename ContainerAllocator2>
bool operator!=(const ::robp_msgs::Encoders_<ContainerAllocator1> & lhs, const ::robp_msgs::Encoders_<ContainerAllocator2> & rhs)
{
  return !(lhs == rhs);
}


} // namespace robp_msgs

namespace ros
{
namespace message_traits
{





template <class ContainerAllocator>
struct IsMessage< ::robp_msgs::Encoders_<ContainerAllocator> >
  : TrueType
  { };

template <class ContainerAllocator>
struct IsMessage< ::robp_msgs::Encoders_<ContainerAllocator> const>
  : TrueType
  { };

template <class ContainerAllocator>
struct IsFixedSize< ::robp_msgs::Encoders_<ContainerAllocator> >
  : FalseType
  { };

template <class ContainerAllocator>
struct IsFixedSize< ::robp_msgs::Encoders_<ContainerAllocator> const>
  : FalseType
  { };

template <class ContainerAllocator>
struct HasHeader< ::robp_msgs::Encoders_<ContainerAllocator> >
  : TrueType
  { };

template <class ContainerAllocator>
struct HasHeader< ::robp_msgs::Encoders_<ContainerAllocator> const>
  : TrueType
  { };


template<class ContainerAllocator>
struct MD5Sum< ::robp_msgs::Encoders_<ContainerAllocator> >
{
  static const char* value()
  {
    return "190037ad3ca3cb2954f783e368d7bd4a";
  }

  static const char* value(const ::robp_msgs::Encoders_<ContainerAllocator>&) { return value(); }
  static const uint64_t static_value1 = 0x190037ad3ca3cb29ULL;
  static const uint64_t static_value2 = 0x54f783e368d7bd4aULL;
};

template<class ContainerAllocator>
struct DataType< ::robp_msgs::Encoders_<ContainerAllocator> >
{
  static const char* value()
  {
    return "robp_msgs/Encoders";
  }

  static const char* value(const ::robp_msgs::Encoders_<ContainerAllocator>&) { return value(); }
};

template<class ContainerAllocator>
struct Definition< ::robp_msgs::Encoders_<ContainerAllocator> >
{
  static const char* value()
  {
    return "Header header\n"
"\n"
"# Total number of ticks\n"
"int64 encoder_left\n"
"int64 encoder_right\n"
"# The number of ticks since the last reading\n"
"int32 delta_encoder_left\n"
"int32 delta_encoder_right\n"
"# The time elapsed since the last reading in milliseconds\n"
"float64 delta_time_left\n"
"float64 delta_time_right\n"
"================================================================================\n"
"MSG: std_msgs/Header\n"
"# Standard metadata for higher-level stamped data types.\n"
"# This is generally used to communicate timestamped data \n"
"# in a particular coordinate frame.\n"
"# \n"
"# sequence ID: consecutively increasing ID \n"
"uint32 seq\n"
"#Two-integer timestamp that is expressed as:\n"
"# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')\n"
"# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')\n"
"# time-handling sugar is provided by the client library\n"
"time stamp\n"
"#Frame this data is associated with\n"
"string frame_id\n"
;
  }

  static const char* value(const ::robp_msgs::Encoders_<ContainerAllocator>&) { return value(); }
};

} // namespace message_traits
} // namespace ros

namespace ros
{
namespace serialization
{

  template<class ContainerAllocator> struct Serializer< ::robp_msgs::Encoders_<ContainerAllocator> >
  {
    template<typename Stream, typename T> inline static void allInOne(Stream& stream, T m)
    {
      stream.next(m.header);
      stream.next(m.encoder_left);
      stream.next(m.encoder_right);
      stream.next(m.delta_encoder_left);
      stream.next(m.delta_encoder_right);
      stream.next(m.delta_time_left);
      stream.next(m.delta_time_right);
    }

    ROS_DECLARE_ALLINONE_SERIALIZER
  }; // struct Encoders_

} // namespace serialization
} // namespace ros

namespace ros
{
namespace message_operations
{

template<class ContainerAllocator>
struct Printer< ::robp_msgs::Encoders_<ContainerAllocator> >
{
  template<typename Stream> static void stream(Stream& s, const std::string& indent, const ::robp_msgs::Encoders_<ContainerAllocator>& v)
  {
    s << indent << "header: ";
    s << std::endl;
    Printer< ::std_msgs::Header_<ContainerAllocator> >::stream(s, indent + "  ", v.header);
    s << indent << "encoder_left: ";
    Printer<int64_t>::stream(s, indent + "  ", v.encoder_left);
    s << indent << "encoder_right: ";
    Printer<int64_t>::stream(s, indent + "  ", v.encoder_right);
    s << indent << "delta_encoder_left: ";
    Printer<int32_t>::stream(s, indent + "  ", v.delta_encoder_left);
    s << indent << "delta_encoder_right: ";
    Printer<int32_t>::stream(s, indent + "  ", v.delta_encoder_right);
    s << indent << "delta_time_left: ";
    Printer<double>::stream(s, indent + "  ", v.delta_time_left);
    s << indent << "delta_time_right: ";
    Printer<double>::stream(s, indent + "  ", v.delta_time_right);
  }
};

} // namespace message_operations
} // namespace ros

#endif // ROBP_MSGS_MESSAGE_ENCODERS_H
