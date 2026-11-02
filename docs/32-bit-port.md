# 32-bit Android porting notes

Status: **not implemented**. The shipping Gradle ABI is still `arm64-v8a`; the manual GitHub Actions build is not a 32-bit build. Android 10+ and a Vulkan 1.1 driver are still required.

## Architectural blocker

The pinned XboxXBE-Recomp runtime (`99078b119b5d5e0d1d6afb1390e29437c0c984c0`) in `runtime/kernel/memory.cpp` reserves a contiguous `1ull << 32` byte range with `mmap`, then overlays two aliases of physical memory within it. A 32-bit Android process cannot reserve a full 4 GiB range alongside its own code, heap, system libraries and OS mappings. Converting the size to 32-bit `size_t` also cannot represent 4 GiB. This is about **virtual address space**, not simply the phone's installed RAM.

This reservation is a pervasive contract: `runtime/cpu/x86_ops.h` computes guest pointers as `base + uint32_t(address)`, including bulk copies, and `runtime/kernel/kernel.h`, other runtime code and game hooks also use base-relative pointers. Adding `armeabi-v7a` to `abiFilters`, reducing the reservation or using a different mmap hint will not preserve that contract.

## Work required

1. Design and implement guest address translation (e.g. a segmented/sparse mapping) for 32-bit hosts in a maintained SDK fork. Preserve guest wraparound, pointer lifetimes and the physical/write-combined alias, including accesses crossing mapping boundaries. Audit all direct `base + guest` accesses in the runtime, generated code, port hooks and graphics/audio paths; bulk operations require range-aware handling too.
2. Update the recompiler and generated code wherever they assume a flat host pointer. Audit atomic, alignment and unaligned x86 memory operations and multithreading, and 32-bit host-size, integer and pointer conversions throughout all dependencies. Validate Vulkan handles and shader/compiler support for `armeabi-v7a`.
3. Only after the runtime works, enable `armeabi-v7a` (keeping arm64), ensure every packaged `.so` exists for each ABI, and add CI tests for ELF headers and installation. Check 32-bit virtual address and memory pressure, not just build success.
4. Run guest-memory tests for boundary crossings, aliases, allocations, deallocation, protection and concurrency. Run a real-device or emulator 32-bit installation, boot and gameplay/save/load tests on a device with a compatible Vulkan 1.1 driver; separately regression-test arm64. A successful compilation alone does not prove compatibility.

The existing encrypted XBE requires the `XBE_KEY` GitHub Actions secret to build; users still need their own legally acquired game files for gameplay. Do not commit the key, decrypted executable, generated game code or game data.
