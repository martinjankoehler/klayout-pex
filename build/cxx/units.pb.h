// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: units.proto
// Protobuf C++ Version: 5.26.1

#ifndef GOOGLE_PROTOBUF_INCLUDED_units_2eproto_2epb_2eh
#define GOOGLE_PROTOBUF_INCLUDED_units_2eproto_2epb_2eh

#include <limits>
#include <string>
#include <type_traits>
#include <utility>

#include "google/protobuf/port_def.inc"
#if PROTOBUF_VERSION != 5026001
#error "Protobuf C++ gencode is built with an incompatible version of"
#error "Protobuf C++ headers/runtime. See"
#error "https://protobuf.dev/support/cross-version-runtime-guarantee/#cpp"
#endif
#include "google/protobuf/port_undef.inc"
#include "google/protobuf/io/coded_stream.h"
#include "google/protobuf/arena.h"
#include "google/protobuf/arenastring.h"
#include "google/protobuf/generated_message_tctable_decl.h"
#include "google/protobuf/generated_message_util.h"
#include "google/protobuf/metadata_lite.h"
#include "google/protobuf/generated_message_reflection.h"
#include "google/protobuf/repeated_field.h"  // IWYU pragma: export
#include "google/protobuf/extension_set.h"  // IWYU pragma: export
#include "google/protobuf/generated_enum_reflection.h"
// @@protoc_insertion_point(includes)

// Must be included last.
#include "google/protobuf/port_def.inc"

#define PROTOBUF_INTERNAL_EXPORT_units_2eproto

namespace google {
namespace protobuf {
namespace internal {
class AnyMetadata;
}  // namespace internal
}  // namespace protobuf
}  // namespace google

// Internal implementation detail -- do not use these members.
struct TableStruct_units_2eproto {
  static const ::uint32_t offsets[];
};
extern const ::google::protobuf::internal::DescriptorTable
    descriptor_table_units_2eproto;
namespace google {
namespace protobuf {
}  // namespace protobuf
}  // namespace google

namespace kpex {
namespace tech {
enum Unit : int {
  MICRO = 0,
  Unit_INT_MIN_SENTINEL_DO_NOT_USE_ =
      std::numeric_limits<::int32_t>::min(),
  Unit_INT_MAX_SENTINEL_DO_NOT_USE_ =
      std::numeric_limits<::int32_t>::max(),
};

bool Unit_IsValid(int value);
extern const uint32_t Unit_internal_data_[];
constexpr Unit Unit_MIN = static_cast<Unit>(0);
constexpr Unit Unit_MAX = static_cast<Unit>(0);
constexpr int Unit_ARRAYSIZE = 0 + 1;
const ::google::protobuf::EnumDescriptor*
Unit_descriptor();
template <typename T>
const std::string& Unit_Name(T value) {
  static_assert(std::is_same<T, Unit>::value ||
                    std::is_integral<T>::value,
                "Incorrect type passed to Unit_Name().");
  return Unit_Name(static_cast<Unit>(value));
}
template <>
inline const std::string& Unit_Name(Unit value) {
  return ::google::protobuf::internal::NameOfDenseEnum<Unit_descriptor,
                                                 0, 0>(
      static_cast<int>(value));
}
inline bool Unit_Parse(absl::string_view name, Unit* value) {
  return ::google::protobuf::internal::ParseNamedEnum<Unit>(
      Unit_descriptor(), name, value);
}

// ===================================================================



// ===================================================================




// ===================================================================


#ifdef __GNUC__
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
#endif  // __GNUC__
#ifdef __GNUC__
#pragma GCC diagnostic pop
#endif  // __GNUC__

// @@protoc_insertion_point(namespace_scope)
}  // namespace tech
}  // namespace kpex


namespace google {
namespace protobuf {

template <>
struct is_proto_enum<::kpex::tech::Unit> : std::true_type {};
template <>
inline const EnumDescriptor* GetEnumDescriptor<::kpex::tech::Unit>() {
  return ::kpex::tech::Unit_descriptor();
}

}  // namespace protobuf
}  // namespace google

// @@protoc_insertion_point(global_scope)

#include "google/protobuf/port_undef.inc"

#endif  // GOOGLE_PROTOBUF_INCLUDED_units_2eproto_2epb_2eh
