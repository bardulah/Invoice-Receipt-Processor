import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class BudgetManager:
    """Manage budgets, track spending, and generate alerts"""

    def __init__(self, data_folder, categorizer):
        self.data_folder = data_folder
        self.categorizer = categorizer
        self.budgets_file = os.path.join(data_folder, 'budgets.json')
        self.alerts_file = os.path.join(data_folder, 'budget_alerts.json')
        self.budgets = self.load_budgets()
        self.alerts = self.load_alerts()

    def load_budgets(self):
        """Load budgets from file"""
        if os.path.exists(self.budgets_file):
            try:
                with open(self.budgets_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_budgets(self):
        """Save budgets to file"""
        with open(self.budgets_file, 'w') as f:
            json.dump(self.budgets, f, indent=2)

    def load_alerts(self):
        """Load alerts from file"""
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_alerts(self):
        """Save alerts to file"""
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)

    def create_budget(self, budget_data):
        """
        Create a new budget
        budget_data = {
            'name': 'Office Supplies Budget',
            'amount': 500.00,
            'period': 'monthly',  # monthly, quarterly, yearly, custom
            'category': 'Office Supplies',  # optional
            'vendor': '',  # optional
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',  # optional for recurring
            'alert_thresholds': [50, 75, 90, 100]  # Alert at these % levels
        }
        """
        budget_id = f"BDG{datetime.now().strftime('%Y%m%d%H%M%S')}"

        budget = {
            'id': budget_id,
            'name': budget_data.get('name', 'Unnamed Budget'),
            'amount': budget_data.get('amount', 0),
            'period': budget_data.get('period', 'monthly'),
            'category': budget_data.get('category'),
            'vendor': budget_data.get('vendor'),
            'start_date': budget_data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
            'end_date': budget_data.get('end_date'),
            'alert_thresholds': budget_data.get('alert_thresholds', [75, 90, 100]),
            'enabled': True,
            'created_date': datetime.now().isoformat(),
            'rollover_unused': budget_data.get('rollover_unused', False)
        }

        self.budgets.append(budget)
        self.save_budgets()

        return budget_id

    def update_budget(self, budget_id, updates):
        """Update an existing budget"""
        for budget in self.budgets:
            if budget['id'] == budget_id:
                budget.update(updates)
                budget['updated_date'] = datetime.now().isoformat()
                self.save_budgets()
                return True
        return False

    def delete_budget(self, budget_id):
        """Delete a budget"""
        self.budgets = [b for b in self.budgets if b['id'] != budget_id]
        self.save_budgets()

    def get_budget(self, budget_id):
        """Get a specific budget"""
        for budget in self.budgets:
            if budget['id'] == budget_id:
                return budget
        return None

    def get_all_budgets(self):
        """Get all budgets"""
        return self.budgets

    def get_active_budgets(self):
        """Get currently active budgets"""
        today = datetime.now().date()
        active = []

        for budget in self.budgets:
            if not budget.get('enabled', True):
                continue

            start_date = datetime.strptime(budget['start_date'], '%Y-%m-%d').date()

            # Check if budget has ended
            if budget.get('end_date'):
                end_date = datetime.strptime(budget['end_date'], '%Y-%m-%d').date()
                if today > end_date:
                    continue

            # Check if budget has started
            if today >= start_date:
                active.append(budget)

        return active

    def calculate_budget_period_dates(self, budget):
        """Calculate the current period's start and end dates for a budget"""
        today = datetime.now().date()
        start_date = datetime.strptime(budget['start_date'], '%Y-%m-%d').date()

        period = budget['period']

        if period == 'monthly':
            # Calculate current month's period
            period_start = today.replace(day=1)
            if today.month == 12:
                period_end = today.replace(day=31)
            else:
                period_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        elif period == 'quarterly':
            # Calculate current quarter
            quarter = (today.month - 1) // 3
            period_start = today.replace(month=quarter*3 + 1, day=1)
            period_end = (period_start + timedelta(days=93)).replace(day=1) - timedelta(days=1)

        elif period == 'yearly':
            # Calculate current year
            period_start = today.replace(month=1, day=1)
            period_end = today.replace(month=12, day=31)

        elif period == 'custom':
            # Use specified dates
            period_start = start_date
            if budget.get('end_date'):
                period_end = datetime.strptime(budget['end_date'], '%Y-%m-%d').date()
            else:
                period_end = today

        else:
            # Default to monthly
            period_start = today.replace(day=1)
            period_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Don't start before budget start date
        period_start = max(period_start, start_date)

        return period_start.strftime('%Y-%m-%d'), period_end.strftime('%Y-%m-%d')

    def get_budget_status(self, budget_id):
        """
        Get current status of a budget
        Returns spending amount, percentage, and status
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return None

        # Get period dates
        start_date, end_date = self.calculate_budget_period_dates(budget)

        # Calculate spending for this period
        filters = {
            'start_date': start_date,
            'end_date': end_date
        }

        if budget.get('category'):
            filters['category'] = budget['category']

        if budget.get('vendor'):
            filters['vendor'] = budget['vendor']

        expenses = self.categorizer.get_expenses(**filters)

        # Calculate total spent
        spent = sum(e.get('amount', 0) for e in expenses)

        # Calculate percentage
        budget_amount = budget['amount']
        percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0

        # Determine status
        if percentage >= 100:
            status = 'exceeded'
        elif percentage >= 90:
            status = 'critical'
        elif percentage >= 75:
            status = 'warning'
        elif percentage >= 50:
            status = 'on_track'
        else:
            status = 'good'

        return {
            'budget_id': budget_id,
            'budget_name': budget['name'],
            'budget_amount': budget_amount,
            'spent': spent,
            'remaining': budget_amount - spent,
            'percentage': percentage,
            'status': status,
            'period_start': start_date,
            'period_end': end_date,
            'expense_count': len(expenses),
            'enabled': budget.get('enabled', True)
        }

    def check_all_budgets(self):
        """
        Check all active budgets and generate alerts if needed
        Returns list of budget statuses and new alerts
        """
        active_budgets = self.get_active_budgets()
        statuses = []
        new_alerts = []

        for budget in active_budgets:
            status = self.get_budget_status(budget['id'])
            if status:
                statuses.append(status)

                # Check if we need to create alerts
                alert_thresholds = budget.get('alert_thresholds', [75, 90, 100])
                percentage = status['percentage']

                for threshold in alert_thresholds:
                    if percentage >= threshold:
                        # Check if we already alerted for this threshold in this period
                        if not self._has_alerted(budget['id'], threshold, status['period_start']):
                            alert = self.create_alert(budget, status, threshold)
                            new_alerts.append(alert)

        return {
            'statuses': statuses,
            'new_alerts': new_alerts,
            'checked_date': datetime.now().isoformat()
        }

    def _has_alerted(self, budget_id, threshold, period_start):
        """Check if we've already sent an alert for this budget/threshold/period"""
        for alert in self.alerts:
            if (alert.get('budget_id') == budget_id and
                alert.get('threshold') == threshold and
                alert.get('period_start') == period_start and
                not alert.get('dismissed', False)):
                return True
        return False

    def create_alert(self, budget, status, threshold):
        """Create a budget alert"""
        alert_id = f"ALT{datetime.now().strftime('%Y%m%d%H%M%S')}"

        severity = 'info'
        if threshold >= 100:
            severity = 'critical'
        elif threshold >= 90:
            severity = 'error'
        elif threshold >= 75:
            severity = 'warning'

        alert = {
            'id': alert_id,
            'budget_id': budget['id'],
            'budget_name': budget['name'],
            'threshold': threshold,
            'percentage': status['percentage'],
            'spent': status['spent'],
            'budget_amount': status['budget_amount'],
            'remaining': status['remaining'],
            'period_start': status['period_start'],
            'period_end': status['period_end'],
            'severity': severity,
            'message': self._generate_alert_message(budget, status, threshold),
            'created_date': datetime.now().isoformat(),
            'dismissed': False,
            'read': False
        }

        self.alerts.append(alert)
        self.save_alerts()

        return alert

    def _generate_alert_message(self, budget, status, threshold):
        """Generate alert message"""
        name = budget['name']
        spent = status['spent']
        budget_amount = status['budget_amount']
        remaining = status['remaining']

        if threshold >= 100:
            return f"Budget Exceeded! {name} has exceeded its budget of ${budget_amount:.2f}. Total spent: ${spent:.2f}"
        elif threshold >= 90:
            return f"Critical: {name} is at {threshold}% of budget (${spent:.2f} of ${budget_amount:.2f}). Only ${remaining:.2f} remaining."
        elif threshold >= 75:
            return f"Warning: {name} has reached {threshold}% of budget. ${remaining:.2f} remaining."
        else:
            return f"Notice: {name} is at {threshold}% of budget."

    def get_alerts(self, unread_only=False, undismissed_only=False):
        """Get budget alerts"""
        alerts = self.alerts

        if unread_only:
            alerts = [a for a in alerts if not a.get('read', False)]

        if undismissed_only:
            alerts = [a for a in alerts if not a.get('dismissed', False)]

        # Sort by date, newest first
        alerts.sort(key=lambda x: x.get('created_date', ''), reverse=True)

        return alerts

    def mark_alert_read(self, alert_id):
        """Mark an alert as read"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['read'] = True
                alert['read_date'] = datetime.now().isoformat()
                self.save_alerts()
                return True
        return False

    def dismiss_alert(self, alert_id):
        """Dismiss an alert"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['dismissed'] = True
                alert['dismissed_date'] = datetime.now().isoformat()
                self.save_alerts()
                return True
        return False

    def get_budget_summary(self):
        """Get summary of all budgets"""
        active_budgets = self.get_active_budgets()
        statuses = [self.get_budget_status(b['id']) for b in active_budgets]

        total_budgeted = sum(s['budget_amount'] for s in statuses if s)
        total_spent = sum(s['spent'] for s in statuses if s)
        total_remaining = total_budgeted - total_spent

        status_counts = defaultdict(int)
        for status in statuses:
            if status:
                status_counts[status['status']] += 1

        return {
            'total_budgets': len(active_budgets),
            'total_budgeted': total_budgeted,
            'total_spent': total_spent,
            'total_remaining': total_remaining,
            'overall_percentage': (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0,
            'by_status': dict(status_counts),
            'active_alerts': len(self.get_alerts(undismissed_only=True)),
            'budgets': statuses
        }

    def get_spending_forecast(self, budget_id):
        """
        Forecast spending for remainder of budget period
        Based on current spending rate
        """
        status = self.get_budget_status(budget_id)
        if not status:
            return None

        period_start = datetime.strptime(status['period_start'], '%Y-%m-%d').date()
        period_end = datetime.strptime(status['period_end'], '%Y-%m-%d').date()
        today = datetime.now().date()

        total_days = (period_end - period_start).days + 1
        days_elapsed = (today - period_start).days + 1
        days_remaining = (period_end - today).days

        if days_elapsed <= 0:
            return None

        # Calculate daily average spending
        daily_avg = status['spent'] / days_elapsed

        # Forecast total spending
        forecasted_total = daily_avg * total_days

        # Calculate if we'll exceed budget
        will_exceed = forecasted_total > status['budget_amount']
        overage = forecasted_total - status['budget_amount'] if will_exceed else 0

        # Recommended daily spending to stay on budget
        if days_remaining > 0:
            recommended_daily = status['remaining'] / days_remaining
        else:
            recommended_daily = 0

        return {
            'budget_id': budget_id,
            'current_spent': status['spent'],
            'budget_amount': status['budget_amount'],
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
            'daily_average': daily_avg,
            'forecasted_total': forecasted_total,
            'will_exceed': will_exceed,
            'forecasted_overage': overage,
            'recommended_daily_spending': recommended_daily,
            'status': 'over_budget' if will_exceed else 'on_track'
        }
