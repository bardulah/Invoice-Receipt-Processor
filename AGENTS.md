# Agent Handoff Document: Invoice-Receipt-Processor

**Last Updated**: 2025-11-10
**Current Agent**: Gemini

---

## 🎯 1. Current Status

### Project Overview
This is a full-stack web application that digitizes and organizes financial documents. Users upload invoices or receipts, and the application uses Optical Character Recognition (OCR) to extract key data, categorize the expense, and organize the files.

### Deployment Status
*   **Status**: ✅ **LIVE**
*   **Platform**: VPS (via PM2)
*   **Live URL**: [https://invoice.curak.xyz](https://invoice.curak.xyz)
*   **Internal Port**: `5001`

### Technology Stack
*   **Backend**: Python, Flask
*   **Frontend**: Vanilla JavaScript, HTML5, CSS3
*   **OCR**: Tesseract, OpenCV, Pillow
*   **Database**: JSON files (used as a simple database).
*   **Infrastructure**: Deployed on a VPS, managed by PM2, with Nginx as a reverse proxy.

### Key Files
*   `INSTRUCTIONS.md`: User-facing guide on how to use the application.
*   `ecosystem.config.js`: (Located in `/opt/deployment/`) PM2 configuration file.
*   `backend/app.py`: The main entry point for the Flask backend.

---

## 🚀 2. Recommended Improvements

This section outlines potential future enhancements for the project.

1.  **Line Item Extraction**: Enhance the OCR process to extract individual line items from invoices, not just the total amount. This would allow for much more granular expense tracking and categorization.
2.  **Direct Accounting Software Integration**: Integrate with software like QuickBooks, Xero, or Wave to automatically sync processed expenses, eliminating manual data entry.
3.  **Email Forwarding**: Set up a dedicated email address where users can forward their email receipts (e.g., from Uber, Amazon). The system would automatically parse the email and process any attachments.
4.  **Mobile App / PWA**: Develop a simple mobile app or enhance the Progressive Web App (PWA) features to allow users to quickly snap photos of physical receipts and upload them on the go.
5.  **Database Upgrade**: Migrate the data storage from flat JSON files to a proper database like SQLite or PostgreSQL. This would significantly improve performance, data integrity, and the ability to run complex queries.

---

## 🤝 3. Agent Handoff Notes

### How to Work on This Project

*   **Deployment**: The application is deployed using **PM2**. The service is configured to run the Flask backend. To restart the live service after making changes, use `pm2 restart invoice-processor`.
*   **Dependencies**: Python dependencies are managed in `requirements.txt`. If you add a new dependency, you will need to install it on the server using `pip install --break-system-packages <package-name>` before restarting the PM2 service.
*   **System Dependencies**: This project has a critical system-level dependency on the **Tesseract OCR engine**. If the OCR functionality fails, ensure that Tesseract is still installed and accessible on the server's PATH.
*   **Data Storage**: Be aware that the "database" is just a collection of JSON files in the `data/` directory. This is simple but not robust. Any work on the project should consider the limitations of this approach.
*   **Updating Documentation**: If you make any user-facing changes, update the `INSTRUCTIONS.md` file. If you make architectural changes, update this `AGENTS.md` file.

### What to Watch Out For

*   **OCR Accuracy**: The accuracy of the Tesseract OCR engine can vary greatly depending on the quality of the uploaded image. The image preprocessing steps in `backend/extractor.py` are critical.
*   **File Permissions**: The application writes to the `uploads/` and `processed/` directories. Ensure that the user running the PM2 process has the correct write permissions for these folders.
*   **Frontend and Backend are Separate**: The frontend consists of static HTML, CSS, and JS files that communicate with the Flask backend via API calls. Changes to the frontend require editing the files in the `frontend/` directory directly.
