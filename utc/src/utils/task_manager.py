import subprocess
from multiprocessing import Pool, current_process
from multiprocessing.pool import ApplyResult
from psutil import Process, cpu_count
from subprocess import Popen, call, TimeoutExpired, DEVNULL, SubprocessError
from shlex import split as cmd_split
from typing import List, Callable, Tuple, Any, Optional


class TaskManager:
    """
    Class handling processing tasks with multiprocessing
    """
    def __init__(self, processes: int, tasks: List[Tuple[Callable, Tuple[Any]]] = None):
        """
        :param processes: number of parallel processes
        :param tasks: task given to task manager, optional
        """
        self._processes = self.set_processes(processes, True)
        # (function, args), ...
        self.tasks: List[Tuple[Callable, tuple]] = [] if tasks is None else tasks

    def start(self, processes: int = None) -> List[Any]:
        """
        :param processes: num processes to be used
        :return: Results from tasks in list (same order as in the tasks)
        """
        results: List[ApplyResult] = []
        if processes is not None:
            self.set_processes(processes)
        elif not self.tasks:
            print("Cannot start multiprocessing tasks with empty task list!")
            return results
        # Save opening of pool
        with Pool(self._processes) as pool:
            for (func, args) in self.tasks:
                results.append(pool.apply_async(func, args=args))
            self.tasks.clear()
            # Close pool
            pool.close()
            pool.join()
        return [res.get() for res in results]

    @staticmethod
    def call_shell(command: str, timeout: float = None, cwd: str = None, message: bool = True) -> Tuple[bool, int]:
        """
        https://stackoverflow.com/questions/41094707/setting-timeout-when-using-os-system-function
        Used Popen from subprocess module to enable multiple processes running in parallel and
        to kill any subprocesses created by calling given command.

        :param command: console/terminal command string
        :param timeout: total time (seconds) for running the console command (default None -> till done)
        :param cwd: directory from which command should be called from (default is current)
        :param message: true if called command should be printed & its success result, default true
        :return: True/False on success/failure, return value of process
        """
        if message:
            print(f"Calling command: '{cmd_split(command)}' with timeout: '{timeout}', cwd: {cwd}")
            print(f"On process: {current_process().name}")
        assert(timeout is None or timeout > 0.0)
        success: bool = False
        ret_val: int = -1
        proc: Optional[Popen[str]] = None
        try:
            proc = Popen(cmd_split(command), stdout=DEVNULL, stdin=DEVNULL, cwd=cwd, encoding="utf-8")
            ret_val = proc.wait(timeout)
            if proc.poll() is not None:
                success = True
        except SubprocessError as e:
            # Kill process and any children it has
            if proc is not None:
                print(f"Process: {current_process().name} ran out of time, killing process ..")
                process = Process(proc.pid)
                for proc in process.children(recursive=True):
                    proc.kill()
                process.kill()
            # Catch other errors, apart from timeout ...
            if not isinstance(e, TimeoutExpired):
                print(f"Error:! {e}")
            else:
                success = True
        if message:
            print(f"Successfully executed command: {success}")
        return success, ret_val

    @staticmethod
    def call_shell_block(command: str, cwd: str = None, message: bool = True) -> Tuple[bool, int]:
        """
        Calls the given command using subprocess.call function which blocks the entire
        processes till the task is finished.

        :param command: console/terminal command string
        :param cwd: directory from which command should be called from (default is current)
        :param message: true if called command should be printed & its success result, default true
        :return: True/False on success/failure, return value of process
        """
        if message:
            print(f"Calling command: '{cmd_split(command)}' cwd: {cwd}")
            print(f"On process: {current_process().name}")
        success: bool = False
        ret_val: int = -1
        try:
            ret_val = call(cmd_split(command), stdout=DEVNULL, stdin=DEVNULL, cwd=cwd)
            success = True
        except SubprocessError as e:
            print(f"Error:! {e}")
        if message:
            print(f"Successfully executed command: {success}")
        return success, ret_val

    # ------------------------------ Utils ------------------------------

    def set_processes(self, processes: int, check: bool = True) -> int:
        """
        :param processes: number of parallel processes
        :param check: if the given count should be checked
        :return: number of processes (minimal 1, max equal to the CPU core count)
        """
        if check:
            self.check_process_count(processes)
        self._processes = min(max(processes, 1), self.get_max_processes())
        return self._processes

    def check_thread_count(self, threads: int) -> bool:
        """"
        :param threads: number of threads
        :return: true if number is correct, false otherwise
        """
        if threads < 1:
            print(f"Thread count cannot be lower than 1, got: {threads} !")
            return False
        elif threads > cpu_count():
            print(f"Thread count cannot be higher than: {cpu_count()}, got: {threads}")
            return False
        return True

    def check_process_count(self, processes: int) -> bool:
        """
        :param processes: number of processes
        :return: true if number is correct, false otherwise
        """
        if processes < 1:
            print(f"Number of processes cannot be lower than 1, got: {processes} !")
            return False
        elif processes > self.get_max_processes():
            print(f"Number of processes cannot be higher than: {cpu_count(logical=FutureWarning)}, got: {processes}")
            return False
        return True

    def get_max_processes(self) -> int:
        """
        :return: maximal amount of process that can be run at the same time
        """
        return cpu_count(logical=False)

