"""
Report Builder Service
======================
Generates month-end reports with CSV and HTML output.
"""

import logging
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..database import get_db
from ..config import get_settings

logger = logging.getLogger(__name__)


class ReportBuilder:
    """Builds month-end reports for senior executive detections."""
    
    def __init__(self):
        """Initialize report builder."""
        self.db = get_db()
        self.settings = get_settings()
    
    def get_pending_reports(self) -> List[dict]:
        """
        Get reports that need file generation.
        
        Returns reports where file_uri is NULL.
        """
        with self.db.get_cursor() as cur:
            cur.execute("""
                SELECT id, month_label, generated_at, rules_version, summary
                FROM reports
                WHERE file_uri IS NULL
                ORDER BY generated_at DESC
                LIMIT 10
            """)
            reports = cur.fetchall()
            logger.info(f"Found {len(reports)} pending reports")
            return reports
    
    def get_report_data(self, month_label: str) -> List[dict]:
        """
        Get detection data for a specific month.
        
        Returns list of users who were detected in that month and joined in that month.
        """
        # Parse month label (e.g., "2025-11")
        year, month = month_label.split('-')
        
        with self.db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    us.user_id,
                    us.username,
                    us.title,
                    us.seniority_level,
                    us.country,
                    us.company,
                    us.joined_at,
                    us.first_detected_at
                FROM user_state us
                WHERE EXTRACT(YEAR FROM us.joined_at) = %s
                  AND EXTRACT(MONTH FROM us.joined_at) = %s
                  AND EXTRACT(YEAR FROM us.first_detected_at) = %s
                  AND EXTRACT(MONTH FROM us.first_detected_at) = %s
                ORDER BY us.first_detected_at DESC
            """, (year, month, year, month))
            
            data = cur.fetchall()
            logger.info(f"Retrieved {len(data)} records for month {month_label}")
            return data
    
    def generate_csv(self, data: List[dict], month_label: str) -> str:
        """
        Generate CSV report.
        
        Returns CSV content as string.
        """
        output = io.StringIO()
        
        if not data:
            # Empty report
            writer = csv.writer(output)
            writer.writerow(['No data for this month'])
            return output.getvalue()
        
        # Define columns
        fieldnames = [
            'User ID', 'Username', 'Title', 'Seniority Level',
            'Country', 'Company', 'Joined At', 'First Detected At'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            writer.writerow({
                'User ID': row['user_id'],
                'Username': row['username'],
                'Title': row['title'],
                'Seniority Level': row['seniority_level'].upper(),
                'Country': row['country'] or 'N/A',
                'Company': row['company'] or 'N/A',
                'Joined At': row['joined_at'].strftime('%Y-%m-%d') if row['joined_at'] else 'N/A',
                'First Detected At': row['first_detected_at'].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return output.getvalue()
    
    def generate_html(self, data: List[dict], month_label: str, summary: Dict[str, Any]) -> str:
        """
        Generate HTML report.
        
        Returns HTML content as string.
        """
        # Build summary stats
        total = summary.get('total_detections', 0)
        csuite = summary.get('csuite_count', 0)
        vp = summary.get('vp_count', 0)
        countries = summary.get('countries', {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Senior Executive Report - {month_label}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #e7f3ff;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #0056b3;
        }}
        .stat {{
            display: inline-block;
            margin-right: 30px;
            font-size: 1.1em;
        }}
        .stat strong {{
            color: #007bff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-csuite {{
            background-color: #28a745;
            color: white;
        }}
        .badge-vp {{
            background-color: #17a2b8;
            color: white;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Senior Executive Detection Report</h1>
        <p><strong>Month:</strong> {month_label}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="stat">
                <strong>Total Detections:</strong> {total}
            </div>
            <div class="stat">
                <strong>C-Suite:</strong> {csuite}
            </div>
            <div class="stat">
                <strong>VP Level:</strong> {vp}
            </div>
        </div>
        
        <h2>Detections</h2>
"""
        
        if not data:
            html += "<p><em>No senior executives detected this month.</em></p>"
        else:
            html += """
        <table>
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Title</th>
                    <th>Level</th>
                    <th>Country</th>
                    <th>Company</th>
                    <th>Joined</th>
                    <th>Detected</th>
                </tr>
            </thead>
            <tbody>
"""
            for row in data:
                level_class = f"badge-{row['seniority_level']}"
                html += f"""
                <tr>
                    <td>{row['username']}</td>
                    <td>{row['title']}</td>
                    <td><span class="badge {level_class}">{row['seniority_level'].upper()}</span></td>
                    <td>{row['country'] or 'N/A'}</td>
                    <td>{row['company'] or 'N/A'}</td>
                    <td>{row['joined_at'].strftime('%Y-%m-%d') if row['joined_at'] else 'N/A'}</td>
                    <td>{row['first_detected_at'].strftime('%Y-%m-%d')}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""
        
        html += """
        <div class="footer">
            <p>This report is generated automatically by CaptPathfinder.</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def save_to_local(self, content: str, filename: str) -> str:
        """
        Save report to local filesystem.
        
        In production, you would upload to Supabase Storage instead.
        Returns file path/URI.
        """
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        filepath = reports_dir / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"Saved report to {filepath}")
        return str(filepath)
    
    def upload_to_supabase_storage(self, content: str, filename: str) -> Optional[str]:
        """
        Upload report to Supabase Storage.
        
        This is a stub - implement actual Supabase Storage upload here.
        Returns public URL or None if failed.
        """
        # TODO: Implement Supabase Storage upload
        # Example using httpx:
        # storage_url = self.settings.supabase_storage_url
        # bucket = self.settings.supabase_storage_bucket
        # 
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{storage_url}/object/{bucket}/{filename}",
        #         content=content,
        #         headers={
        #             "Authorization": f"Bearer {self.settings.supabase_anon_key}",
        #             "Content-Type": "text/html" or "text/csv"
        #         }
        #     )
        #     return response.json()['url']
        
        logger.warning("Supabase Storage upload not implemented, using local storage")
        return self.save_to_local(content, filename)
    
    def generate_report(self, report_id: int, month_label: str, summary: Dict[str, Any]) -> dict:
        """
        Generate complete report (CSV + HTML).
        
        Returns summary with file URIs.
        """
        logger.info(f"Generating report for month {month_label}")
        
        # Get data
        data = self.get_report_data(month_label)
        
        # Generate CSV
        csv_content = self.generate_csv(data, month_label)
        csv_filename = f"report_{month_label}.csv"
        csv_uri = self.save_to_local(csv_content, csv_filename)
        
        # Generate HTML
        html_content = self.generate_html(data, month_label, summary)
        html_filename = f"report_{month_label}.html"
        html_uri = self.save_to_local(html_content, html_filename)
        
        # Update report record with file URIs
        file_uri = f"csv: {csv_uri}, html: {html_uri}"
        
        with self.db.get_cursor() as cur:
            cur.execute("""
                UPDATE reports
                SET file_uri = %s
                WHERE id = %s
            """, (file_uri, report_id))
        
        logger.info(f"Report {report_id} generated successfully")
        
        return {
            "report_id": report_id,
            "month_label": month_label,
            "csv_uri": csv_uri,
            "html_uri": html_uri,
            "record_count": len(data)
        }
    
    def process_pending_reports(self) -> dict:
        """
        Process all pending reports.
        
        Returns summary of results.
        """
        reports = self.get_pending_reports()
        
        results = {
            "total": len(reports),
            "generated": 0,
            "failed": 0,
            "errors": []
        }
        
        for report in reports:
            try:
                result = self.generate_report(
                    report_id=report['id'],
                    month_label=report['month_label'],
                    summary=report['summary'] or {}
                )
                results["generated"] += 1
                logger.info(f"Generated report: {result}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Report {report['id']}: {str(e)}")
                logger.error(
                    f"Error generating report {report['id']}: {e}",
                    exc_info=True
                )
        
        return results


# Singleton instance
_report_builder: Optional[ReportBuilder] = None


def get_report_builder() -> ReportBuilder:
    """Get report builder instance (singleton)."""
    global _report_builder
    if _report_builder is None:
        _report_builder = ReportBuilder()
    return _report_builder

