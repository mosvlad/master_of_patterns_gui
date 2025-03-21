"""
Nesting task model for pattern nesting application.
"""
import os
import time
import re
import subprocess
import threading
from datetime import datetime

from core.parser import parse_ses_file


class NestingTask:
    """Class representing a nesting task"""
    STATUS_WAITING = "Ожидание"
    STATUS_RUNNING = "В процессе"
    STATUS_COMPLETED = "Завершено"
    STATUS_STOPPED = "Прервано"
    STATUS_ERROR = "Ошибка"

    def __init__(self, dxf_file, nesting_program, wrk_file=None, width=50.0, time_limit=5 * 60):
        """
        Initialize a nesting task
        
        Args:
            dxf_file (str): Path to DXF file
            nesting_program (str): Path to nesting program executable
            wrk_file (str, optional): Path to WRK file. If None, generated from DXF path
            width (float, optional): Width for nesting. Defaults to 50.0
            time_limit (int, optional): Time limit in seconds. Defaults to 5 minutes
        """
        self.dxf_file = dxf_file
        self.nesting_program = nesting_program
        self.wrk_file = wrk_file or self._generate_wrk_filename(dxf_file)
        self.width = width
        self.time_limit = time_limit  # In seconds

        self.status = self.STATUS_WAITING
        self.start_time = None
        self.end_time = None
        self.progress_time = 0  # In seconds
        self.efficiency = 0.0
        self.pattern_count = self._count_patterns_in_dxf()
        self.length = 0.0

        # Process control
        self.process = None
        self.thread = None
        self.stop_flag = False
        self.is_running = False

    def _generate_wrk_filename(self, dxf_file):
        """
        Generate a WRK filename from the DXF filename
        
        Args:
            dxf_file (str): Path to DXF file
            
        Returns:
            str: Path to WRK file
        """
        base_dir = os.path.dirname(dxf_file)
        base_name = os.path.splitext(os.path.basename(dxf_file))[0]
        return os.path.join(base_dir, f"{base_name}.wrk")

    def _count_patterns_in_dxf(self):
        """
        Count pattern pieces in the DXF file
        
        Returns:
            int: Number of pattern pieces found
        """
        try:
            # Simple method: count blocks that start with 'B' in the DXF file
            pattern_count = 0

            # Open the DXF file and scan for blocks
            with open(self.dxf_file, 'r', errors='ignore') as f:
                content = f.read()

                # Look for BLOCK entries that start with 'B'
                blocks = re.findall(r'BLOCK\s+2\s+B\d+', content)
                pattern_count = len(blocks)

            return pattern_count
        except Exception as e:
            print(f"Error counting patterns in DXF: {e}")
            return 0

    def start(self):
        """
        Start the nesting task
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_running:
            print("Task is already running")
            return False

        print(f"Starting task for {self.dxf_file}")

        # Generate WRK file if needed
        if not os.path.exists(self.wrk_file):
            if not self._generate_wrk_file():
                self.status = self.STATUS_ERROR
                print("Failed to generate WRK file")
                return False

        # Start the task in a separate thread
        self.stop_flag = False
        self.status = self.STATUS_RUNNING
        self.start_time = datetime.now()
        self.is_running = True

        self.thread = threading.Thread(target=self._run_task)
        self.thread.daemon = True
        self.thread.start()

        print(f"Task started in thread, status: {self.status}")
        return True

    def stop(self):
        """
        Stop the nesting task
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running:
            return False

        self.stop_flag = True
        if self.process:
            try:
                print("Terminating process...")
                self.process.terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")

        self.status = self.STATUS_STOPPED
        self.end_time = datetime.now()
        self.is_running = False
        return True

    def update_progress(self):
        """
        Update the progress time if the task is running
        """
        if self.is_running and self.start_time:
            current_time = datetime.now()
            delta = current_time - self.start_time
            self.progress_time = int(delta.total_seconds())

    def _run_task(self):
        """
        Run the nesting task with robust SES file detection
        Internal method that runs in a separate thread
        """
        try:
            print(f"Running nesting program: {self.nesting_program}")
            print(f"Using WRK file: {self.wrk_file}")

            # Ensure paths are absolute
            nesting_program = os.path.abspath(self.nesting_program)
            wrk_file = os.path.abspath(self.wrk_file)

            # Check if files exist
            if not os.path.exists(nesting_program):
                print(f"Nesting program not found: {nesting_program}")
                self.status = self.STATUS_ERROR
                self.end_time = datetime.now()
                self.is_running = False
                self._notify_task_completed()
                return

            if not os.path.exists(wrk_file):
                print(f"WRK file not found: {wrk_file}")
                if not self._generate_wrk_file():
                    self.status = self.STATUS_ERROR
                    self.end_time = datetime.now()
                    self.is_running = False
                    self._notify_task_completed()
                    return

            # Determine expected SES file path - multiple ways to construct it
            dxf_basename = os.path.splitext(os.path.basename(self.dxf_file))[0]
            dxf_dir = os.path.dirname(self.dxf_file)
            ses_file_paths = [
                os.path.join(dxf_dir, f"{dxf_basename}.ses"),
                os.path.join(os.path.dirname(wrk_file), f"{dxf_basename}.ses")
            ]

            # Print the file paths we'll be checking
            for path in ses_file_paths:
                print(f"Will check for SES file at: {path}")

            # Check if SES file already exists before starting (to detect changes)
            ses_exists_before = any(os.path.exists(path) for path in ses_file_paths)
            if ses_exists_before:
                # Store modification times of existing files
                ses_mtimes_before = {}
                for path in ses_file_paths:
                    if os.path.exists(path):
                        ses_mtimes_before[path] = os.path.getmtime(path)
                        print(f"Existing SES file found at {path} with mtime {ses_mtimes_before[path]}")

            # Set working directory to the nesting program directory
            program_dir = os.path.dirname(nesting_program)

            # Create process
            import platform
            if platform.system() == 'Windows':
                try:
                    self.process = subprocess.Popen(
                        [nesting_program, wrk_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=program_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                except Exception as e:
                    print(f"Process creation without shell failed: {e}")
                    self.process = subprocess.Popen(
                        f'"{nesting_program}" "{wrk_file}"',
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=program_dir,
                        shell=True
                    )
            else:
                self.process = subprocess.Popen(
                    [nesting_program, wrk_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=program_dir
                )

            if not self.process:
                print("Failed to create process")
                self.status = self.STATUS_ERROR
                self.end_time = datetime.now()
                self.is_running = False
                self._notify_task_completed()
                return

            print(f"Process started with PID: {self.process.pid}")

            # Initialize start time and progress
            start_time = time.time()
            self.progress_time = 0
            process_terminated = False

            # Wait for process to complete with progress updates
            while self.process.poll() is None:
                # Check if we should stop
                if self.stop_flag:
                    print("Stop flag detected, terminating process")
                    self.process.terminate()
                    process_terminated = True
                    break

                # Update progress time
                current_time = time.time()
                self.progress_time = int(current_time - start_time)

                # Check if we've exceeded the time limit
                if self.progress_time >= self.time_limit:
                    print(f"Time limit ({self.time_limit}s) reached, terminating process")
                    self.process.terminate()
                    process_terminated = True
                    break

                # Check if SES file has appeared while process is running
                # This helps in cases where the process creates the file but doesn't exit
                for ses_path in ses_file_paths:
                    if os.path.exists(ses_path):
                        # Check if it's new or modified
                        if ses_exists_before and ses_path in ses_mtimes_before:
                            # Check if modified
                            current_mtime = os.path.getmtime(ses_path)
                            if current_mtime > ses_mtimes_before[ses_path]:
                                print(f"SES file {ses_path} was modified during processing")
                        else:
                            print(f"New SES file detected at {ses_path} during processing")

                # Sleep to avoid busy waiting
                time.sleep(0.1)

            # Process has completed or was terminated
            return_code = self.process.poll()
            try:
                stdout, stderr = self.process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                print("Process did not communicate within timeout, forcing termination")
                self.process.kill()
                stdout, stderr = self.process.communicate()
                return_code = -1

            # Calculate final time
            elapsed = time.time() - start_time
            minutes = int(elapsed) // 60
            seconds = int(elapsed) % 60
            print(f"Process completed in {minutes}:{seconds:02d}")

            # Wait a short time to ensure any file operations have completed
            print("Waiting for file operations to complete...")
            time.sleep(1)

            # Check for SES file existence - more thoroughly this time
            ses_file_exists = False
            ses_file_path = None

            for path in ses_file_paths:
                print(f"Checking for SES file at: {path}")
                if os.path.exists(path):
                    file_size = os.path.getsize(path)
                    file_mtime = os.path.getmtime(path)
                    mtime_str = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"SES file found at {path}, size={file_size} bytes, modified={mtime_str}")

                    # Check if file was just created/modified (within last minute)
                    if not ses_exists_before or path not in ses_mtimes_before or file_mtime > ses_mtimes_before[path]:
                        print(f"SES file at {path} is new or was modified during processing")
                        ses_file_exists = True
                        ses_file_path = path
                        break
                    else:
                        print(f"SES file at {path} exists but wasn't modified during processing")

            if not ses_file_exists:
                # One more check - look for any .ses files in the directory
                for file in os.listdir(dxf_dir):
                    if file.endswith('.ses') and file.startswith(dxf_basename):
                        full_path = os.path.join(dxf_dir, file)
                        print(f"Found alternative SES file: {full_path}")
                        ses_file_exists = True
                        ses_file_path = full_path
                        break

            print(f"Final SES file exists check result: {ses_file_exists}")

            # Update status based on result
            if self.stop_flag:
                self.status = self.STATUS_STOPPED
                print("Process was stopped by user")
            elif ses_file_exists:
                # If the SES file exists, consider the task completed successfully
                self.status = self.STATUS_COMPLETED
                print(f"Process completed successfully - SES file found at {ses_file_path}")

                # Use the found SES path for parsing
                self._parse_results(ses_file_path)
            elif return_code == 0:
                self.status = self.STATUS_COMPLETED
                print("Process completed successfully with exit code 0")
            else:
                # Check one last time if SES file exists in any location
                final_check = any(os.path.exists(path) for path in ses_file_paths)
                if final_check:
                    self.status = self.STATUS_COMPLETED
                    print("Final check found SES file exists, marking as completed")
                    # Find the path that exists
                    for path in ses_file_paths:
                        if os.path.exists(path):
                            self._parse_results(path)
                            break
                else:
                    self.status = self.STATUS_ERROR
                    print(f"Process failed with error code {return_code}")
                    if stderr:
                        print(f"Error output: {stderr[:500]}")

            self.end_time = datetime.now()
            self.is_running = False

            # Signal the UI that we're done
            self._notify_task_completed()

        except Exception as e:
            import traceback
            print(f"Error running nesting task: {e}")
            traceback.print_exc()
            self.status = self.STATUS_ERROR
            self.end_time = datetime.now()
            self.is_running = False
            self._notify_task_completed()

    def _notify_task_completed(self):
        """
        Notify that the task has completed
        This method is meant to be overridden by the task manager
        """
        pass

    def _generate_wrk_file(self):
        """
        Generate a WRK file for the nesting program
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Generating WRK file: {self.wrk_file}")

            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.wrk_file), exist_ok=True)

            with open(self.wrk_file, 'w') as f:
                f.write("NESTING-WORK-FILE\n")

                # Get directory paths
                dxf_dir = os.path.dirname(self.dxf_file)
                wrk_dir = os.path.dirname(self.wrk_file)

                # Write file paths
                f.write(f"CHDIR {wrk_dir}\n")
                f.write(f"IMPORT DXF {self.dxf_file}\n")
                f.write("BUILD_NEST 0\n")
                f.write("BEGIN_TASK\n")
                f.write(f"MARKER_FILE_DIRECTORY  {wrk_dir}\n")
                f.write(f"SESSION_FILE_DIRECTORY {wrk_dir}\n")

                # Get the filename without extension
                dxf_basename = os.path.splitext(os.path.basename(self.dxf_file))[0]

                # Add marker file section
                f.write("BEGIN_MARKER_FILE\n")
                f.write(f"{dxf_basename}.dat\n")
                f.write("END_MARKER_FILE\n")

                # Add automatic actions
                f.write("BEGIN_AUTOMATIC_ACTIONS\n")
                time_limit_minutes = self.time_limit // 60
                f.write(f"NEST_COMPLETE MIN_EFF=0 MAX_EFF=100 TIME={time_limit_minutes} ")
                f.write("NUM_SAVE=1 OPTIONALS=10\n")
                f.write("END_AUTOMATIC_ACTIONS\n")
                f.write("END_TASK\n")

                # Export session file
                ses_file = os.path.join(dxf_dir, f"{dxf_basename}.ses")
                f.write(f"EXPORT dxf {ses_file}\n")
                f.write("END_WORK_FILE\n")

            print(f"WRK file generated successfully: {self.wrk_file}")
            return True
        except Exception as e:
            import traceback
            print(f"Error generating WRK file: {e}")
            traceback.print_exc()
            return False

    def _parse_results(self, ses_file_path=None):
        """
        Parse the results from the SES file
        
        Args:
            ses_file_path (str, optional): Path to SES file. If None, constructed from DXF path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the SES file path
            if ses_file_path is None:
                dxf_basename = os.path.splitext(os.path.basename(self.dxf_file))[0]
                dxf_dir = os.path.dirname(self.dxf_file)
                ses_file_path = os.path.join(dxf_dir, f"{dxf_basename}.ses")

            print(f"Parsing results from SES file: {ses_file_path}")

            if not os.path.exists(ses_file_path):
                print(f"SES file not found: {ses_file_path}")
                return False

            # Use parse_ses_file function from core.parser
            nesting_data = parse_ses_file(ses_file_path)

            if nesting_data and 'marker_info' in nesting_data:
                # Extract efficiency
                if 'efficiency' in nesting_data['marker_info']:
                    self.efficiency = nesting_data['marker_info']['efficiency']
                    print(f"Extracted efficiency: {self.efficiency}")

                # Extract length
                if 'length' in nesting_data['marker_info']:
                    self.length = nesting_data['marker_info']['length']
                    print(f"Extracted length: {self.length}")

                # Count pattern pieces
                if 'pieces' in nesting_data:
                    self.pattern_count = len(nesting_data['pieces'])
                    print(f"Counted {self.pattern_count} pattern pieces")
                
                return True
            
            # If parse_ses_file returned None or incomplete data, fall back to basic parsing
            print("Basic parsing result data due to missing information")
            
            with open(ses_file_path, 'r', errors='ignore') as f:
                content = f.read()

                # Extract marker efficiency
                if "MARKER_EFFICIENCY" in content:
                    efficiency_match = re.search(r'MARKER_EFFICIENCY\s+(\d+(\.\d+)?)', content)
                    if efficiency_match:
                        self.efficiency = float(efficiency_match.group(1))
                        print(f"Extracted efficiency: {self.efficiency}")

                # Alternative efficiency format
                elif "EFFICIENCY:" in content:
                    efficiency_match = re.search(r'EFFICIENCY:\s+(\d+(\.\d+)?)', content)
                    if efficiency_match:
                        self.efficiency = float(efficiency_match.group(1))
                        print(f"Extracted efficiency (alt format): {self.efficiency}")

                # Extract marker length
                if "MARKER_LENGTH" in content:
                    length_match = re.search(r'MARKER_LENGTH\s+(\d+(\.\d+)?)', content)
                    if length_match:
                        self.length = float(length_match.group(1))
                        print(f"Extracted length: {self.length}")

                # Alternative length format
                elif "HEIGHT:" in content:
                    length_match = re.search(r'HEIGHT:\s+(\d+(\.\d+)?)', content)
                    if length_match:
                        self.length = float(length_match.group(1))
                        print(f"Extracted length (alt format): {self.length}")

                # Count pattern pieces
                if self.pattern_count == 0 and "BEGIN_PIECE" in content:
                    self.pattern_count = content.count("BEGIN_PIECE")
                    print(f"Counted {self.pattern_count} pattern pieces")
                
                return True

        except Exception as e:
            import traceback
            print(f"Error parsing SES file: {e}")
            traceback.print_exc()
            return False