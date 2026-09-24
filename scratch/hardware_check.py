import os
import shutil
import platform
import subprocess

def check_hardware():
    print("=== SYSTEM HARDWARE & RESOURCE CHECK REPORT ===")

    # 1. OS & Architecture
    arch = platform.architecture()[0]
    machine = platform.machine()
    system = platform.system()
    release = platform.release()
    print(f"9. Windows Architecture: {system} {release} ({arch}, machine={machine})")

    # 2. Disk Space on workspace drive
    workspace_drive = os.path.splitdrive(r"C:\Users\user\OneDrive\Desktop\mynotes-rag")[0] or "C:"
    total, used, free = shutil.disk_usage(workspace_drive)
    total_gb = round(total / (1024**3), 2)
    free_gb = round(free / (1024**3), 2)
    print(f"8. Free Disk Space on drive {workspace_drive}: {free_gb} GB free out of {total_gb} GB total")

    # 3. RAM and System info via systeminfo / powershell
    try:
        ps_ram = subprocess.check_output(
            ["powershell", "-Command", "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize; (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"],
            text=True
        ).strip().splitlines()
        total_ram_gb = round(int(ps_ram[0].strip()) / (1024 * 1024), 2)
        free_ram_gb = round(int(ps_ram[1].strip()) / (1024 * 1024), 2)
        print(f"1. Total System RAM: {total_ram_gb} GB")
        print(f"2. Available/Free RAM: {free_ram_gb} GB")
    except Exception as e:
        print(f"1 & 2. RAM query error: {e}")

    # 4. CPU Info
    try:
        cpu_name = subprocess.check_output(
            ["powershell", "-Command", "(Get-CimInstance Win32_Processor).Name"],
            text=True
        ).strip()
        cores = subprocess.check_output(
            ["powershell", "-Command", "(Get-CimInstance Win32_Processor).NumberOfCores"],
            text=True
        ).strip()
        threads = subprocess.check_output(
            ["powershell", "-Command", "(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors"],
            text=True
        ).strip()
        print(f"3. CPU Model: {cpu_name}")
        print(f"4. CPU Core/Thread Count: {cores} Cores / {threads} Threads")
    except Exception as e:
        print(f"3 & 4. CPU query error: {e}")

    # 5. GPU & VRAM & CUDA Check
    try:
        gpu_names = subprocess.check_output(
            ["powershell", "-Command", "(Get-CimInstance Win32_VideoController).Name"],
            text=True
        ).strip().splitlines()
        gpu_str = ", ".join([g.strip() for g in gpu_names if g.strip()])
        print(f"5. GPU Model(s): {gpu_str}")
    except Exception as e:
        print(f"5. GPU query error: {e}")

    # Check CUDA / VRAM via PyTorch / nvidia-smi
    cuda_avail = False
    vram_info = "N/A (No Dedicated NVIDIA VRAM)"
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        if cuda_avail:
            gpu_device = torch.cuda.get_device_name(0)
            vram_bytes = torch.cuda.get_device_properties(0).total_memory
            vram_gb = round(vram_bytes / (1024**3), 2)
            vram_info = f"{vram_gb} GB VRAM ({gpu_device})"
    except Exception:
        pass

    if not cuda_avail:
        try:
            nvidia_smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            if nvidia_smi.returncode == 0:
                cuda_avail = True
                vram_info = "NVIDIA GPU detected via nvidia-smi"
        except Exception:
            pass

    print(f"6. GPU VRAM: {vram_info}")
    print(f"7. NVIDIA CUDA GPU Available: {cuda_avail}")

if __name__ == "__main__":
    check_hardware()
