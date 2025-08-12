#!/usr/bin/env python3
"""
Watch for new files in the current active wandb project.
This script monitors the wandb project for new files matching a specified regex pattern.
Defaults to "model_*.pt" pattern.
"""

import os
import time
import re
import wandb
from wandb.apis.public import Run, File
from typing import Set, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WandbFileWatcher:
    """Monitor wandb project for new model files."""
    
    def __init__(self, project_name: Optional[str] = None, run_name: Optional[str] = None, pattern: str = r"model_.*\.pt", download_dir: Optional[str] = None):
        """
        Initialize the file watcher.
        
        Args:
            project_name: Optional project name. If None, uses the active project.
            pattern: Regex pattern to match files (default: "model_.*\\.pt")
        """
        self.project_name = project_name
        self.run_name = run_name
        self.download_dir = download_dir
        self.api = wandb.Api()
        self.new_files: dict[str, File] = {}
        self.known_files: dict[str, File] = {}
        self.pattern = re.compile(pattern)
        self.run: Run = self.get_run()

    def get_run(self) -> Run:
        """Get the run from the path."""
        try:
            if self.run_name:
                filters = {"config.experiment_name": self.run_name}
            else:
                filters = None
            runs = self.api.runs(self.project_name, filters=filters, order="-created_at")
            return next(runs)
        except Exception as e:
            logger.error(f"Error getting run from path {self.project_name}: {e}")
            raise
    
    def update(self) -> dict[str, File]:
        """Get all files in the current wandb project."""
        try:
            logger.info(f"Monitoring project: {self.project_name}")
            
            # Get the project
            self.known_files.update(self.new_files)
            self.new_files = {}
            
            try:
                run_files = self.run.files()
                for file in run_files:
                    if self.pattern.match(file.name):
                        if file.name not in self.known_files and file.name not in self.new_files:
                            self.new_files[file.name] = file
                            logger.debug(f"New file: {file.name}")
                            if self.download_dir:
                                if not os.path.exists(self.download_dir):
                                    os.makedirs(self.download_dir)
                                path = os.path.join(self.download_dir, self.run.name)
                                file.download(root=path)
            except Exception as e:
                logger.warning(f"Error getting files from run {self.run.id}: {e}")
            
            return self.new_files
            
        except Exception as e:
            logger.error(f"Error getting project files: {e}")
            return {}

    def watch(self, check_interval: int = 30):
        """
        Start watching for new files matching the pattern.
        
        Args:
            check_interval: Time between checks in seconds (default: 30)
        """
        logger.info("Starting wandb file watcher...")
        logger.info(f"Looking for files matching pattern: {self.pattern.pattern}")
        logger.info(f"Check interval: {check_interval} seconds")
        
        # Initialize known files
        logger.info(f"Found {len(self.known_files)} existing files")
        
        try:
            while True:
                new_files = self.update()
                
                if new_files:
                    logger.info(f"Found {len(new_files)} new matching file(s):")
                    for file in new_files:
                        logger.info(f"New matching file detected: {file}")
                else:
                    logger.info("No new files found")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("File watcher stopped by user")
        except Exception as e:
            logger.error(f"Error in file watcher: {e}")
            raise

def main():
    """Main function to run the file watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Watch for new files in wandb project")
    parser.add_argument("--project_name", type=str, help="Wandb project name")
    parser.add_argument("--run_name", type=str, help="Wandb run name")
    parser.add_argument("--download_dir", default=None, type=str, help="Directory to download files to (default: None)")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds (default: 30)")
    parser.add_argument("--pattern", type=str, default=r"model_.*\.pt", help="Regex pattern to match files (default: model_.*\\.pt)")
    
    args = parser.parse_args()
    
    try:
        watcher = WandbFileWatcher(project_name=args.project_name, run_name=args.run_name, pattern=args.pattern, download_dir=args.download_dir)
        watcher.watch(check_interval=args.interval)
    except Exception as e:
        logger.error(f"Failed to start file watcher: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
