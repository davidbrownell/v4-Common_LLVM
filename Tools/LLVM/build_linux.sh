#!/bin/bash
# ----------------------------------------------------------------------
# |
# |  build_linux.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-14 13:16:14
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
set -e                                      # Exit on error
set -x                                      # Statements

# Builds LLVM code using docker
#
# Docker command:
#
#   CentOS 8 Image [OFFICIAL RELEASE]
#   ---------------------------------
#       [Linux Host]     docker run -it --rm -v `pwd`/..:/local centos:8 bash /local/LLVM/build_linux.sh <3.10.6>
#       [Windows Host]   docker run -it --rm -v %cd%\..:/local  centos:8 bash /local/LLVM/build_linux.sh <3.10.6>
#
#   Holy Build Box Image
#   --------------------
#   NOTE THAT THIS DOESN'T WORK RIGHT NOW with optimizations, errors during build
#
#       [Linux Host]     docker run -it --rm -v `pwd`/..:/local phusion/holy-build-box-64 bash /local/LLVM/build_linux.sh <3.10.6>
#       [Windows Host]   docker run -it --rm -v %cd%\..:/local  phusion/holy-build-box-64 bash /local/LLVM/build_linux.sh <3.10.6>
#

if [[ "$1" == "15.0.2" ]]
then
    LLVM_VERSION=15.0.2
    LLVM_VERSION_SHORT=15.0
    LLVM_VERSION_SHORTER=15

else
    echo "Invalid LLVM version; expected 15.0.2"
    exit
fi

is_centos_8=0
is_hbb=0

if [[ -e /hbb_exe/activate-exec ]];
then
    is_hbb=1
elif [[ `cat /etc/centos-release` == *release[[:space:]]8* ]]
then
    is_centos_8=1
fi

# no_clean=1

UpdateEnvironment()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |"
    echo "# |  Updating Development Environment"
    echo "# |"
    echo "# ----------------------------------------------------------------------"
    set -x

    if [[ ${is_hbb} == 1 ]];
    then
        /hbb_exe/activate-exec
    else
        if [[ ${is_centos_8} == 1 ]];
        then
            sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
            sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
        fi

        yum update -y
        yum groupinstall -y "Development Tools"
        yum install -y epel-release
    fi

    yum install -y \
        binutils-devel \
        bzip2-devel \
        ccache \
        p7zip \
        python3
}

InstallCMake()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |"
    echo "# |  Installing CMake"
    echo "# |"
    echo "# ----------------------------------------------------------------------"
    set -x

    [[ -e /src/cmake-3.24.2-linux-x86_64/bin ]] || curl -L https://github.com/Kitware/CMake/releases/download/v3.24.2/cmake-3.24.2-linux-x86_64.tar.gz  | gunzip -c | tar xf -
    export PATH=/src/cmake-3.24.2-linux-x86_64/bin:${PATH}
}

InstallNinja()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |"
    echo "# |  Installing Ninja"
    echo "# |"
    echo "# ----------------------------------------------------------------------"
    set -x

    if [[ ! -e /src/ninja ]]; then
        curl -L https://github.com/ninja-build/ninja/releases/download/v1.11.1/ninja-linux.zip --output ninja.zip
        unzip -q ninja.zip
    fi

    export PATH=/src:${PATH}
}

BuildLLVM()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |"
    echo "# |  Building LLVM"
    echo "# |"
    echo "# ----------------------------------------------------------------------"
    set -x

    [[ ! -e /opt/Common_LLVM/llvm/${LLVM_VERSION} ]] || rm -rfd /opt/Common_LLVM/llvm/${LLVM_VERSION}

    if [[ -e llvm-project-llvmorg-${LLVM_VERSION} && no_clean -ne 1 ]]; then
        rm -rfd llvm-project-llvmorg-${LLVM_VERSION}
    fi

    if [[ ! -e llvm-project-llvmorg-${LLVM_VERSION} ]]; then
        curl -L https://github.com/llvm/llvm-project/archive/refs/tags/llvmorg-${LLVM_VERSION}.tar.gz | gunzip -c | tar xf -
    fi

    pushd llvm-project-llvmorg-${LLVM_VERSION} > /dev/null

    [[ -e build ]] || mkdir build
    pushd build > /dev/null

    cmake_standard_args="-Wno-dev
        -DCMAKE_BUILD_TYPE=Release
        -DLLVM_CCACHE_BUILD=ON
        -DLLVM_ENABLE_BINDINGS=OFF
        -DLLVM_ENABLE_OCAMLDOC=OFF
        -DLLVM_ENABLE_PLUGINS=OFF
        -DLLVM_ENABLE_WARNINGS=OFF
        -DLLVM_INCLUDE_DOCS=OFF
        -DLLVM_INCLUDE_EXAMPLES=OFF
        -DLLVM_INCLUDE_TESTS=OFF
        "

    set +x
    echo ""
    echo "[36m[1m-------------------------[0m"
    echo "[36m[1m| Building Stage 1 of 3 |[0m"
    echo "[36m[1m-------------------------[0m"
    echo ""
    set -x

    # This step builds LLVM and clang via gcc/ld/libstdc++

    if [[ -e stage1 && no_clean -ne 1 ]]; then
        rm -rfd stage1
    fi

    [[ -e stage1 ]] || mkdir stage1

    pushd stage1 > /dev/null

    cmake -G Ninja -S ../../llvm \
        ${cmake_standard_args} \
        -DCMAKE_C_COMPILER=/usr/bin/gcc \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DLLVM_ENABLE_PROJECTS="clang;lld;" \
        -DLLVM_INSTALL_TOOLCHAIN_ONLY=ON \
        -DLLVM_TARGETS_TO_BUILD="Native" \
        -DLLVM_USE_LINKER=gold


    ninja
    ninja install
    ldconfig

    popd > /dev/null

    set +x
    echo ""
    echo "[36m[1m-------------------------[0m"
    echo "[36m[1m| Building Stage 2 of 3 |[0m"
    echo "[36m[1m-------------------------[0m"
    echo ""
    set -x

    # This step builds LLVM, clang, and runtimes using the clang compiler created in step 1

    if [[ -e stage2 && no_clean -ne 1 ]]; then
        rm -rfd stage2
    fi

    [[ -e stage2 ]] || mkdir stage2

    pushd stage2 > /dev/null

    cmake -G Ninja -S ../../llvm \
        ${cmake_standard_args} \
        -DCMAKE_C_COMPILER=clang \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DCMAKE_SHARED_LINKER_FLAGS="${LDFLAGS}" \
        -DCMAKE_MODULE_LINKER_FLAGS="${LDFLAGS}" \
        -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS}" \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DBUILTINS_CMAKE_ARGS="-DLLVM_ENABLE_PER_TARGET_RUNTIME_DIR=OFF" \
        -DRUNTIMES_CMAKE_ARGS="-DLLVM_ENABLE_PER_TARGET_RUNTIME_DIR=OFF" \
        -DCLANG_DEFAULT_RTLIB=compiler-rt \
        -DCLANG_DEFAULT_CXX_STDLIB=libc++ \
        -DCLANG_DEFAULT_LINKER=lld \
        -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra;libc;lld;" \
        -DLLVM_ENABLE_RUNTIMES="compiler-rt;libcxx;libcxxabi;libunwind;" \
        -DLLVM_INSTALL_TOOLCHAIN_ONLY=ON \
        -DLLVM_TARGETS_TO_BUILD="Native" \
        -DLIBCXX_HAS_ATOMIC_LIB=OFF \
        -DLIBCXX_USE_COMPILER_RT=ON \
        -DLIBCXX_USE_LLVM_UNWINDER=ON \
        -DLIBCXXABI_HAS_GCC_LIB=OFF \
        -DLIBCXXABI_USE_COMPILER_RT=ON \
        -DLIBCXXABI_USE_LLVM_UNWINDER=ON \
        -DLIBUNWIND_USE_COMPILER_RT=ON

    ninja
    ninja install
    ldconfig

    popd > /dev/null

    set +x
    echo ""
    echo "[36m[1m-------------------------[0m"
    echo "[36m[1m| Building Stage 3 of 3 |[0m"
    echo "[36m[1m-------------------------[0m"
    echo ""
    set -x

    # This step builds LLVM, clang, and runtimes using the clang compiler and libraries built in step 2; there should not be any traces of GCC when this is done

    if [[ -e stage3 && no_clean -ne 1 ]]; then
        rm -rfd stage3
    fi

    [[ -e stage3 ]] || mkdir stage3

    pushd stage3 > /dev/null

    export LDFLAGS="-rtlib=compiler-rt -unwindlib=libunwind -stdlib=libc++ -L/usr/local/lib"
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib

    cmake -G Ninja -S ../../llvm \
        ${cmake_standard_args} \
        -DCMAKE_C_COMPILER=clang \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DCMAKE_SHARED_LINKER_FLAGS="${LDFLAGS}" \
        -DCMAKE_MODULE_LINKER_FLAGS="${LDFLAGS}" \
        -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS}" \
        -DCMAKE_INSTALL_PREFIX=/opt/Common_LLVM/llvm/${LLVM_VERSION} \
        -DCLANG_DEFAULT_LINKER=lld \
        -DCLANG_DEFAULT_RTLIB=compiler-rt \
        -DCLANG_DEFAULT_UNWINDLIB=libunwind \
        -DCLANG_DEFAULT_CXX_STDLIB=libc++ \
        -DCLANG_VENDOR="v4-Common_LLVM" \
        -DLIBCXX_HAS_GCC_LIB=OFF \
        -DLIBCXX_USE_COMPILER_RT=ON \
        -DLIBCXX_USE_LLVM_UNWINDER=ON \
        -DLIBCXXABI_HAS_GCC_LIB=OFF \
        -DLIBCXXABI_USE_COMPILER_RT=ON \
        -DLIBCXXABI_USE_LLVM_UNWINDER=ON \
        -DLIBUNWIND_HAS_GCC_LIB=OFF \
        -DLIBUNWIND_USE_COMPILER_RT=ON \
        -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra;libc;lld;" \
        -DLLVM_ENABLE_RUNTIMES="compiler-rt;libcxx;libcxxabi;libunwind;" \
        -DLLVM_INSTALL_TOOLCHAIN_ONLY=OFF \
        -DLLVM_TARGETS_TO_BUILD="X86;" \
        -DLLVM_USE_LINKER=lld \
        -DSANITIZER_CXX_ABI=libc++ \

    ninja
    ninja install

    popd > /dev/null                        # build
    popd > /dev/null                        # llvm-project-llvmorg-${LLVM_VERSION}

    # Zip the output
    pushd /opt/Common_LLVM/llvm/${LLVM_VERSION} > /dev/null                 # install dir

    7za a install.7z *
    cp --force install.7z /local
    rm --force install.7z
}

[[ -d /src ]] || mkdir /src
pushd /src > /dev/null

UpdateEnvironment
InstallCMake
InstallNinja
BuildLLVM

popd > /dev/null

set +x
echo "DONE!"
