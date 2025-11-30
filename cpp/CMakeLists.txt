cmake_minimum_required(VERSION 3.15)
project(DicomToolsCpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(CTest)

# Add local deps install dir to prefix path
list(APPEND CMAKE_PREFIX_PATH "${CMAKE_SOURCE_DIR}/deps/install")

set(DICOMTOOLS_INPUT_DIR "${CMAKE_SOURCE_DIR}/input")

# --- Find Packages ---

# ITK
find_package(ITK QUIET)
if(ITK_FOUND)
    message(STATUS "Found ITK: ${ITK_VERSION}")
    add_compile_definitions(USE_ITK)
else()
    message(WARNING "ITK not found. ITK tests will be disabled.")
endif()

# VTK
find_package(VTK QUIET)
if(VTK_FOUND)
    message(STATUS "Found VTK: ${VTK_VERSION}")
    add_compile_definitions(USE_VTK)
else()
    message(WARNING "VTK not found. VTK tests will be disabled.")
endif()

# DCMTK
find_package(DCMTK QUIET)
if(DCMTK_FOUND)
    message(STATUS "Found DCMTK: ${DCMTK_VERSION}")
    add_compile_definitions(USE_DCMTK)
else()
    message(WARNING "DCMTK not found. DCMTK tests will be disabled.")
endif()

# GDCM
find_package(GDCM QUIET)
if(GDCM_FOUND)
    message(STATUS "Found GDCM: ${GDCM_VERSION}")
else()
    message(WARNING "GDCM not found. GDCM tests will be disabled.")
endif()

# --- Shared include paths ---
set(DICOMTOOLS_INCLUDE_ROOT "${CMAKE_SOURCE_DIR}/src")

# --- Core/CLI library ---
add_library(dicom_cli STATIC
    src/cli/CLIParser.cpp
    src/cli/CommandRegistry.cpp
    src/utils/FileSystemUtils.cpp
)
target_include_directories(dicom_cli PUBLIC ${DICOMTOOLS_INCLUDE_ROOT})
target_compile_definitions(dicom_cli PUBLIC INPUT_DIR="${DICOMTOOLS_INPUT_DIR}")

# --- Module libraries (compile even when deps missing; runtime stubs handle absence) ---
add_library(module_gdcm STATIC
    src/modules/GDCM/GDCMTests.cpp
    src/modules/GDCM/GDCMFeatureActions.cpp
)
target_include_directories(module_gdcm PUBLIC ${DICOMTOOLS_INCLUDE_ROOT})
if(GDCM_FOUND)
    target_compile_definitions(module_gdcm PRIVATE USE_GDCM)
    if(GDCM_INCLUDE_DIRS)
        target_include_directories(module_gdcm PUBLIC ${GDCM_INCLUDE_DIRS})
    else()
        include(${GDCM_USE_FILE})
    endif()
    target_link_libraries(module_gdcm PUBLIC ${GDCM_LIBRARIES})
endif()

add_library(module_dcmtk STATIC
    src/modules/DCMTK/DCMTKTests.cpp
    src/modules/DCMTK/DCMTKFeatureActions.cpp
)
target_include_directories(module_dcmtk PUBLIC ${DICOMTOOLS_INCLUDE_ROOT})
if(DCMTK_FOUND)
    target_compile_definitions(module_dcmtk PRIVATE USE_DCMTK)
    target_include_directories(module_dcmtk PUBLIC ${DCMTK_INCLUDE_DIRS})
    if(APPLE AND EXISTS "/opt/homebrew/lib")
        target_link_directories(module_dcmtk PRIVATE "/opt/homebrew/lib")
    endif()
    target_link_libraries(module_dcmtk PUBLIC ${DCMTK_LIBRARIES})
endif()

add_library(module_itk STATIC
    src/modules/ITK/ITKTests.cpp
    src/modules/ITK/ITKFeatureActions.cpp
)
target_include_directories(module_itk PUBLIC ${DICOMTOOLS_INCLUDE_ROOT})
if(ITK_FOUND)
    target_compile_definitions(module_itk PRIVATE USE_ITK)
    target_link_libraries(module_itk PUBLIC ${ITK_LIBRARIES})
endif()

add_library(module_vtk STATIC
    src/modules/VTK/VTKTests.cpp
    src/modules/VTK/VTKFeatureActions.cpp
)
target_include_directories(module_vtk PUBLIC ${DICOMTOOLS_INCLUDE_ROOT})
if(VTK_FOUND)
    target_compile_definitions(module_vtk PRIVATE USE_VTK)
    target_link_libraries(module_vtk PUBLIC ${VTK_LIBRARIES})
endif()

# --- Executable ---
add_executable(DicomTools src/main.cpp)
target_include_directories(DicomTools PRIVATE ${DICOMTOOLS_INCLUDE_ROOT})
target_compile_definitions(DicomTools PRIVATE INPUT_DIR="${DICOMTOOLS_INPUT_DIR}")
target_link_libraries(DicomTools
    PRIVATE
        dicom_cli
        module_gdcm
        module_dcmtk
        module_itk
        module_vtk
)

if(ITK_FOUND)
    target_compile_definitions(DicomTools PRIVATE USE_ITK)
endif()

if(VTK_FOUND)
    target_compile_definitions(DicomTools PRIVATE USE_VTK)
endif()

if(DCMTK_FOUND)
    target_compile_definitions(DicomTools PRIVATE USE_DCMTK)
    if(DCMTK_LIBRARY_DIR)
        target_link_directories(DicomTools PRIVATE ${DCMTK_LIBRARY_DIR})
    elseif(DCMTK_LIBRARY_DIRS)
        target_link_directories(DicomTools PRIVATE ${DCMTK_LIBRARY_DIRS})
    endif()
    target_link_libraries(DicomTools PRIVATE ${DCMTK_LIBRARIES})
endif()

if(GDCM_FOUND)
    target_compile_definitions(DicomTools PRIVATE USE_GDCM)
    if(GDCM_LIBRARY_DIRS)
        target_link_directories(DicomTools PRIVATE ${GDCM_LIBRARY_DIRS})
    endif()
    target_link_libraries(DicomTools PRIVATE ${GDCM_LIBRARIES})
endif()

if(BUILD_TESTING)
    find_package(Python3 COMPONENTS Interpreter)
    if(Python3_Interpreter_FOUND)
        add_test(
            NAME cpp_run_all
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/run_all.py
            WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        )
    else()
        message(WARNING "Python3 not found; skipping cpp_run_all ctest")
    endif()

    # --- C++ Unit Tests ---
    
    # GDCM Tests
    add_executable(test_gdcm tests/test_gdcm.cpp)
    target_include_directories(test_gdcm PRIVATE ${CMAKE_SOURCE_DIR}/tests)
    if(GDCM_FOUND)
        target_compile_definitions(test_gdcm PRIVATE USE_GDCM)
        if(GDCM_INCLUDE_DIRS)
            target_include_directories(test_gdcm PRIVATE ${GDCM_INCLUDE_DIRS})
        else()
            include(${GDCM_USE_FILE})
        endif()
        target_link_libraries(test_gdcm PRIVATE ${GDCM_LIBRARIES})
    endif()
    add_test(NAME GDCM_Tests COMMAND test_gdcm WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

    # DCMTK Tests
    add_executable(test_dcmtk tests/test_dcmtk.cpp)
    target_include_directories(test_dcmtk PRIVATE ${CMAKE_SOURCE_DIR}/tests)
    if(DCMTK_FOUND)
        target_compile_definitions(test_dcmtk PRIVATE USE_DCMTK)
        target_include_directories(test_dcmtk PRIVATE ${DCMTK_INCLUDE_DIRS})
        if(APPLE AND EXISTS "/opt/homebrew/lib")
            target_link_directories(test_dcmtk PRIVATE "/opt/homebrew/lib")
        endif()
        target_link_libraries(test_dcmtk PRIVATE ${DCMTK_LIBRARIES})
    endif()
    add_test(NAME DCMTK_Tests COMMAND test_dcmtk WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

    # ITK Tests
    add_executable(test_itk tests/test_itk.cpp)
    target_include_directories(test_itk PRIVATE ${CMAKE_SOURCE_DIR}/tests)
    if(ITK_FOUND)
        target_compile_definitions(test_itk PRIVATE USE_ITK)
        target_link_libraries(test_itk PRIVATE ${ITK_LIBRARIES})
    endif()
    add_test(NAME ITK_Tests COMMAND test_itk WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

    # VTK Tests
    add_executable(test_vtk tests/test_vtk.cpp)
    target_include_directories(test_vtk PRIVATE ${CMAKE_SOURCE_DIR}/tests)
    if(VTK_FOUND)
        target_compile_definitions(test_vtk PRIVATE USE_VTK)
        target_link_libraries(test_vtk PRIVATE ${VTK_LIBRARIES})
    endif()
    add_test(NAME VTK_Tests COMMAND test_vtk WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

    # Combined test runner
    add_custom_target(run_cpp_tests
        COMMAND $<TARGET_FILE:test_gdcm>
        COMMAND $<TARGET_FILE:test_dcmtk>
        COMMAND $<TARGET_FILE:test_itk>
        COMMAND $<TARGET_FILE:test_vtk>
        DEPENDS test_gdcm test_dcmtk test_itk test_vtk
        COMMENT "Running all C++ library tests"
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    )
endif()
