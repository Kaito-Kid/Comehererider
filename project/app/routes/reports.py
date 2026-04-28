"""
Reporting system routes for ComeHere Rider (CHR).
Handles user reports, rider reports, and bug reports per plan.md Section H.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db, limiter
from app.models import Report, User, Rider, Consumer, Order
from app.utils.decorators import admin_required, manager_required

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/create', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
@login_required
def create():
    """
    Create a report (user report, rider report, or bug report).
    Per plan.md: Users can report via profile pages, bugs via settings.
    """
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        reported_user_id = request.form.get('reported_user_id')
        related_order_id = request.form.get('related_order_id')
        category = request.form.get('category')
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not all([report_type, category, title, description]):
            flash('Please fill in all required fields.', 'error')
            return render_template('reports/create.html')
        
        # Validate report type
        if report_type not in ['user_report', 'rider_report', 'bug_report']:
            flash('Invalid report type.', 'error')
            return render_template('reports/create.html')
        
        # For user/rider reports, need reported user
        if report_type in ['user_report', 'rider_report'] and not reported_user_id:
            flash('Please specify who you are reporting.', 'error')
            return render_template('reports/create.html')
        
        try:
            report = Report(
                report_type=report_type,
                reporter_id=current_user.id,
                reported_user_id=int(reported_user_id) if reported_user_id else None,
                related_order_id=int(related_order_id) if related_order_id else None,
                category=category,
                title=title,
                description=description,
                status='pending'
            )
            
            db.session.add(report)
            db.session.commit()
            
            flash('Report submitted successfully. We will review it shortly.', 'success')
            
            if current_user.role_type == 'consumer':
                return redirect(url_for('user.dashboard'))
            elif current_user.role_type == 'rider':
                return redirect(url_for('rider.dashboard'))
            else:
                return redirect(url_for('main.index'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to submit report: {str(e)}', 'error')
    
    # Get context for form
    reported_user_id = request.args.get('user_id')
    reported_user = None
    if reported_user_id:
        reported_user = User.query.get(reported_user_id)
    
    order_id = request.args.get('order_id')
    order = None
    if order_id:
        order = Order.query.get(order_id)
    
    return render_template('reports/create.html', 
                         reported_user=reported_user,
                         order=order)


@reports_bp.route('/')
@login_required
def list_reports():
    """
    List reports based on user role.
    Per plan.md: Managers handle user/rider reports, admins handle bugs.
    """
    if current_user.role_type == 'admin':
        # Admins see all reports, especially bug reports
        reports = Report.query.order_by(Report.created_at.desc()).all()
        return render_template('admin/reports.html', reports=reports)
    
    elif current_user.role_type == 'manager':
        # Managers see reports they need to handle
        if current_user.can_manage_riders():
            # Rider Manager sees rider reports
            reports = Report.query.filter_by(report_type='rider_report').order_by(Report.created_at.desc()).all()
        elif current_user.can_manage_consumers():
            # Consumer Manager sees user reports
            reports = Report.query.filter_by(report_type='user_report').order_by(Report.created_at.desc()).all()
        else:
            # Head Manager sees all user and rider reports
            reports = Report.query.filter(
                Report.report_type.in_(['user_report', 'rider_report'])
            ).order_by(Report.created_at.desc()).all()
        
        return render_template('manager/reports.html', reports=reports)
    
    else:
        # Regular users see their own reports
        reports = Report.query.filter_by(reporter_id=current_user.id).order_by(Report.created_at.desc()).all()
        
        if current_user.role_type == 'consumer':
            return render_template('user/my_reports.html', reports=reports)
        else:
            return render_template('rider/my_reports.html', reports=reports)


@reports_bp.route('/<int:report_id>')
@login_required
def detail(report_id):
    """View report details."""
    report = Report.query.get_or_404(report_id)
    
    # Check permissions
    can_view = False
    
    if current_user.role_type == 'admin':
        can_view = True
    elif current_user.role_type == 'manager':
        # Managers can view reports they handle
        if report.report_type == 'rider_report' and current_user.can_manage_riders():
            can_view = True
        elif report.report_type == 'user_report' and current_user.can_manage_consumers():
            can_view = True
        elif current_user.manager_type == 'head':
            can_view = True
    elif report.reporter_id == current_user.id:
        # Users can view their own reports
        can_view = True
    
    if not can_view:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('reports/detail.html', report=report)


@reports_bp.route('/<int:report_id>/handle', methods=['GET', 'POST'])
@limiter.limit("50 per minute")
@login_required
def handle(report_id):
    """
    Handle a report (admin or manager only).
    Assign handler, update status, add resolution notes.
    """
    report = Report.query.get_or_404(report_id)
    
    # Check permissions
    can_handle = False
    
    if current_user.role_type == 'admin':
        can_handle = True
    elif current_user.role_type == 'manager':
        if report.report_type == 'rider_report' and current_user.can_manage_riders():
            can_handle = True
        elif report.report_type == 'user_report' and current_user.can_manage_consumers():
            can_handle = True
        elif current_user.manager_type == 'head':
            can_handle = True
    
    if not can_handle:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        resolution_notes = request.form.get('resolution_notes')
        
        if action == 'assign':
            report.assign_handler(current_user)
            flash('Report assigned to you.', 'success')
        
        elif action == 'resolve':
            if not resolution_notes:
                flash('Please provide resolution notes.', 'error')
                return render_template('reports/handle.html', report=report)
            report.resolve(resolution_notes)
            flash('Report resolved successfully.', 'success')
        
        elif action == 'dismiss':
            if not resolution_notes:
                flash('Please provide reason for dismissal.', 'error')
                return render_template('reports/handle.html', report=report)
            report.dismiss(resolution_notes)
            flash('Report dismissed.', 'info')
        
        db.session.commit()
        return redirect(url_for('reports.detail', report_id=report.id))
    
    return render_template('reports/handle.html', report=report)


@reports_bp.route('/user/<int:user_id>')
@login_required
def report_user(user_id):
    """
    Report a user/rider (accessible from profile pages).
    Per plan.md: Report button on profile pages.
    """
    user = User.query.get_or_404(user_id)
    
    # Can't report yourself
    if user.id == current_user.id:
        flash('You cannot report yourself.', 'error')
        return redirect(url_for('main.index'))
    
    # Determine report type
    if user.role_type == 'rider':
        report_type = 'user_report'  # Consumer reporting a rider
    else:
        report_type = 'rider_report'  # Rider reporting a consumer
    
    return render_template('reports/create.html',
                         reported_user=user,
                         report_type=report_type)


@reports_bp.route('/bug')
@login_required
def bug_report():
    """
    Bug report form (accessible from settings).
    Per plan.md: Bug reports found in settings page.
    """
    return render_template('reports/create.html', report_type='bug_report')
