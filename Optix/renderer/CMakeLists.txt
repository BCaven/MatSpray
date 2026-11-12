# ======================================================================== #
# Copyright 2018-2019 Ingo Wald                                            #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
# ======================================================================== #

find_package(OpenGL REQUIRED)

include_directories(${OptiX_INCLUDE})

# cuda_compile_and_embed(embedded_ptx_code devicePrograms.cu)
embed_ptx(
    OUTPUT_TARGET embedded_ptx_code
    SOURCES devicePrograms.cu
    EMBEDDED_SYMBOL_NAMES embedded_ptx_code
)

target_include_directories(embedded_ptx_code_ptx PRIVATE
    "${OptiX_INSTALL_DIR}/include"
)

# slang_compile_and_embed(embedded_ptx_code2 ${PROJECT_SOURCE_DIR}/renderer/devicePrograms.slang
# )
# compiling the .slang shader to .ptx prior to building.
# ------------------------------------------------------------
# Compile Slang shader to PTX
# ------------------------------------------------------------

find_program(SLANGC_EXECUTABLE
    NAMES slangc
    HINTS "$ENV{SLANG_DIR}/bin"
    REQUIRED
)

set(SLANG_SOURCE
    ${CMAKE_CURRENT_SOURCE_DIR}/devicePrograms.slang
)

set(SLANG_PTX
    ${CMAKE_CURRENT_BINARY_DIR}/devicePrograms.ptx
)

add_custom_command(
    OUTPUT ${SLANG_PTX}

    COMMAND ${SLANGC_EXECUTABLE}
        -target ptx
        -I"${OptiX_INSTALL_DIR}/include"
        ${SLANG_SOURCE}
        -o ${SLANG_PTX}

    DEPENDS ${SLANG_SOURCE}
    VERBATIM
    COMMENT "Compiling Slang shader to PTX"
)

add_custom_target(compile_slang_ptx
    DEPENDS ${SLANG_PTX}
)

# ------------------------------------------------------------
# Embed Slang PTX
# ------------------------------------------------------------

set(EMBEDDED_SLANG_CPP
    ${CMAKE_CURRENT_BINARY_DIR}/embedded_ptx_code2.cpp
)

add_custom_command(
    OUTPUT ${EMBEDDED_SLANG_CPP}
    COMMAND ${CMAKE_COMMAND}
        "-DOBJECTS=${SLANG_PTX}"
        "-DSYMBOL_NAMES=embedded_ptx_code2"
        "-DOUTPUT=${EMBEDDED_SLANG_CPP}"
        -P ${EMBED_PTX_DIR}/run_bin2c.cmake
    DEPENDS ${SLANG_PTX}
    VERBATIM
    COMMENT "Embedding Slang PTX"
)

add_custom_target(generate_slang_ptx
    DEPENDS ${EMBEDDED_SLANG_CPP}
)



find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)
find_package(nanobind CONFIG REQUIRED)

add_library(slang_stuff SHARED
        ${EMBEDDED_SLANG_CPP}
        helperFunctionsDevice.cu
        helperFunctionsDevice.h
        optix7.h
        CUDABuffer.h
        LaunchParams.h
        SampleRenderer.h
        SampleRenderer.cpp
        Model.h
        Model.cpp
)

add_dependencies(slang_stuff generate_slang_ptx)

target_link_libraries(slang_stuff
        PUBLIC
        gdt
        embedded_ptx_code
        # optix dependencies, for rendering
        ${optix_LIBRARY}
        ${CUDA_LIBRARIES}
        ${CUDA_CUDA_LIBRARY}
        # glfw and opengl, for display
        glfWindow
        glfw
        ${OPENGL_gl_LIBRARY}
)

add_executable(run_renderer
        main.cpp
)

target_link_libraries(run_renderer slang_stuff)

