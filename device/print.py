# printer.py
import cups
import logging
import os
from env import EnvConfig

logger = logging.getLogger(__name__)

class Printer:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._printer_name = None
        self._conn = None
        self._load_config()
        self._connect_cups()
    
    def _load_config(self):
        """Load printer configuration from environment"""
        printer_config = self._config.get_printer_config()
        self._printer_name = printer_config.get('name')
        
        if not self._printer_name:
            logger.warning("Printer name not found in environment")
        else:
            logger.info(f"Printer configuration loaded - Name: {self._printer_name}")
    
    def _connect_cups(self):
        """Connect to CUPS server"""
        try:
            self._conn = cups.Connection()
            logger.info("Successfully connected to CUPS server")
        except Exception as e:
            logger.error(f"Failed to connect to CUPS server: {str(e)}")
            self._conn = None
    
    def print_pdf(self, pdf_path, color=True):
        """
        Print PDF file using CUPS
        
        Args:
            pdf_path (str): Path to PDF file
            color (bool): Color printing
            
        Returns:
            tuple: (success, job_id) - job_id is None if failed
        """
        if not self._conn:
            logger.error("CUPS connection not available")
            return False, None
        
        if not self._printer_name:
            logger.error("Printer name not configured")
            return False, None
        
        # Check if PDF file exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return False, None
        
        if not pdf_path.lower().endswith('.pdf'):
            logger.error("File is not a PDF")
            return False, None
        
        try:
            # Build print options
            print_options = {
                "media": "A4",
                "fit-to-page": "true",
                "copies": "1",
            }
            
            print_options["sides"] = "one-sided"
            
            # Add color setting
            if not color:
                print_options["ColorModel"] = "Gray"
            
            # Submit print job
            job_id = self._conn.printFile(
                self._printer_name,
                pdf_path,
                f"PDF Print: {os.path.basename(pdf_path)}",
                print_options
            )
            
            logger.info(f"PDF print job submitted successfully")
            logger.info(f"File: {pdf_path}, Printer: {self._printer_name}, Job ID: {job_id}")
            
            return True, job_id
            
        except cups.IPPError as e:
            logger.error(f"CUPS IPP error while printing: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error printing PDF: {str(e)}")
            return False, None
    
    def get_job_status(self, job_id):
        """
        Get print job status
        
        Args:
            job_id (int): Print job ID
            
        Returns:
            dict: Job status information
        """
        if not self._conn:
            return {"error": "CUPS connection not available"}
        
        try:
            job_attrs = self._conn.getJobAttributes(job_id)
            
            status_info = {
                "job_id": job_id,
                "state": job_attrs.get('job-state', 'unknown'),
                "state_reason": job_attrs.get('job-state-reasons', ''),
                "printer_name": job_attrs.get('printer-uri', ''),
                "document_name": job_attrs.get('job-name', ''),
                "submitted_time": job_attrs.get('time-at-creation', ''),
                "completed_time": job_attrs.get('time-at-completed', ''),
            }
            
            # Map state codes to human readable
            state_map = {
                3: 'pending',
                4: 'held',
                5: 'processing',
                6: 'stopped',
                7: 'canceled',
                8: 'aborted',
                9: 'completed'
            }
            status_info['state_name'] = state_map.get(status_info['state'], 'unknown')
            
            return status_info
            
        except cups.IPPError as e:
            return {"error": f"Job not found: {e}"}
        except Exception as e:
            return {"error": str(e)}
    
    def cancel_all_jobs(self, printer_name=None):
        """
        Cancel all print jobs for a printer
        
        Args:
            printer_name (str): Printer name, uses configured printer if None
            
        Returns:
            bool: True if successful
        """
        if not self._conn:
            logger.error("CUPS connection not available")
            return False
        
        printer_to_use = printer_name or self._printer_name
        if not printer_to_use:
            logger.error("No printer specified")
            return False
        
        try:
            # Get all jobs for the printer
            jobs = self._conn.getJobs(which_jobs='not-completed')
            cancelled_count = 0
            
            for job_id, job_info in jobs.items():
                if job_info.get('printer-uri', '').endswith(printer_to_use):
                    self._conn.cancelJob(job_id)
                    cancelled_count += 1
            
            logger.info(f"Cancelled {cancelled_count} jobs for printer {printer_to_use}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling all jobs: {str(e)}")
            return False
    
    @property
    def is_configured(self):
        """Check if printer is properly configured"""
        return bool(self._printer_name) and self._conn is not None
    
    @property
    def printer_name(self):
        """Get printer name"""
        return self._printer_name


# Test function
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Printer control with python-cups...")
    
    printer = Printer()
    
    # Check configuration
    print(f"Printer configured: {printer.is_configured}")
    if printer.is_configured:
        print(f"Printer Name: {printer.printer_name}")

        print("\n3. Testing PDF printing...")
        pdf_file = "./1.pdf"  # Replace with actual PDF file
        success, job_id = printer.print_pdf(pdf_file, False)
        if success:
            print(f"Print job submitted: {job_id}")
            # Check job status
            
            job_status = printer.get_job_status(job_id)
            print(f"Job status: {job_status}")
        else:
            print("Print job failed")
        
    else:
        print("Printer not configured properly. Please check .env file")


if __name__ == "__main__":
    main()