import ctypes
import importlib
import os
import platform
import sys
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENVIRONMENT_PATH = PROJECT_ROOT / "configs" / "environment"
MODEL_NAME = "yolo26n.pt"
PACKAGE_NAMES = (
    "torch",
    "ultralytics",
    "cv2",
    "numpy",
    "pandas",
    "matplotlib",
    "yaml",
)


# 바이트 단위의 메모리 크기를 사람이 읽기 쉬운 형식으로 변환한다.
def format_bytes(size: int) -> str:
    gibibytes = size / (1024**3)
    return f"{gibibytes:.2f} GiB"


# 운영체제별 표준 API를 사용해 전체 물리 메모리 크기를 조회한다.
def get_total_ram() -> str:
    try:
        if sys.platform == "win32":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_physical", ctypes.c_ulonglong),
                    ("available_physical", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong),
                    ("available_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("available_virtual", ctypes.c_ulonglong),
                    ("available_extended_virtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                raise ctypes.WinError()
            return format_bytes(status.total_physical)

        page_size = os.sysconf("SC_PAGE_SIZE")
        physical_pages = os.sysconf("SC_PHYS_PAGES")
        return format_bytes(page_size * physical_pages)
    except (AttributeError, OSError, ValueError) as error:
        return f"Unavailable ({error})"


# Python과 하드웨어를 포함한 기본 실행 환경 정보를 출력한다.
def print_system_information() -> None:
    cpu = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER")
    cpu = cpu or platform.machine() or "Unknown"

    print("System Information")
    print(f"  Python : {platform.python_version()}")
    print(f"  OS     : {platform.platform()}")
    print(f"  CPU    : {cpu}")
    print(f"  RAM    : {get_total_ram()}")


# 주요 패키지를 모두 불러오고 패키지별 성공 여부를 출력한다.
def import_packages() -> tuple[dict[str, ModuleType], list[tuple[str, Exception]]]:
    modules = {}
    failures = []

    print("\nPackage Imports")
    for package_name in PACKAGE_NAMES:
        try:
            module = importlib.import_module(package_name)
            modules[package_name] = module
            version = getattr(module, "__version__", "version unavailable")
            print(f"  {package_name:<12}: SUCCESS ({version})")
        except Exception as error:  # Import hooks may raise errors beyond ImportError.
            failures.append((package_name, error))
            print(f"  {package_name:<12}: FAILED")

    return modules, failures


# PyTorch가 인식한 연산 장치와 GPU 메모리 정보를 출력한다.
def print_device_information(torch_module: ModuleType) -> None:
    print("\nCompute Device")
    cuda_available = torch_module.cuda.is_available()
    print(f"  CUDA Available : {'Yes' if cuda_available else 'No'}")
    if not cuda_available:
        print("  Device         : CPU")
        return

    device_index = torch_module.cuda.current_device()
    properties = torch_module.cuda.get_device_properties(device_index)
    print("  Device         : GPU")
    print(f"  GPU            : {properties.name}")
    print(f"  VRAM           : {format_bytes(properties.total_memory)}")


# 확정된 기준 YOLO 모델을 불러와 사용 가능 여부를 확인한다.
def check_model_loading(ultralytics_module: ModuleType) -> bool:
    print("\nPretrained Model")
    try:
        ultralytics_module.YOLO(MODEL_NAME)
    except Exception as error:
        print(f"  {MODEL_NAME}: FAILED ({type(error).__name__}: {error})")
        return False

    print(f"  {MODEL_NAME}: SUCCESS")
    return True


# 환경 폴더를 준비하고 전체 환경 진단을 수행한다.
def main() -> int:
    ENVIRONMENT_PATH.mkdir(parents=True, exist_ok=True)

    print_system_information()
    modules, failures = import_packages()

    if failures:
        print("\nPackage import failures:", file=sys.stderr)
        for package_name, error in failures:
            print(
                f"  {package_name}: {type(error).__name__}: {error}",
                file=sys.stderr,
            )

    if "torch" in modules:
        print_device_information(modules["torch"])
    else:
        print("\nCompute Device\n  Device : unavailable (torch import failed)")

    if "ultralytics" in modules:
        model_loaded = check_model_loading(modules["ultralytics"])
    else:
        print("\nPretrained Model\n  Check skipped (ultralytics import failed).")
        model_loaded = False

    return 1 if failures or not model_loaded else 0


if __name__ == "__main__":
    sys.exit(main())
