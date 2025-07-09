from flask import jsonify, render_template, request
from app import db
from sqlalchemy import func, distinct, and_, text
from datetime import datetime, date
import pandas as pd

def page_routes(app):

    @app.route('/')
    def index():    
        return render_template('index.html')
    
    @app.route('/location')
    def location():
        return render_template('location.html')
    
    @app.route('/categories')
    def categories():
        return render_template('categories.html')
    
    @app.route('/types')
    def types():
        return render_template('types.html')
    
    @app.route('/skills')
    def skills():
        return render_template('skills.html')
    
def api_routes(app):
    jobs = db.metadata.tables['jobs']

    @app.route('/api/getDefaultDateRange')
    def get_default_date_range():
        try:
            # Get the earliest and latest dates with data from both sources
            start_date = db.session.query(
                func.min(func.date(jobs.c.date_posted))
            ).filter(
                jobs.c.source.in_(['jobstreet','ricebowl'])
            ).scalar()

            end_date = db.session.query(
                func.max(func.date(jobs.c.date_posted))
            ).filter(
                jobs.c.source.in_(['jobstreet','ricebowl'])
            ).scalar()

            return jsonify({
                'startDate': start_date.strftime('%Y-%m-%d') if start_date else None,
                'endDate': end_date.strftime('%Y-%m-%d') if end_date else None
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getDashboardStats')
    def get_dashboard_stats():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
              # Total jobs
            total_jobs = db.session.query(func.count(jobs.c.id)).filter(and_(*filters)).scalar()
            
            # Total companies
            total_companies = db.session.query(func.count(distinct(jobs.c.company_name))).filter(and_(*filters)).scalar()
            
            # Get table references for job types and categories
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            job_categories = db.metadata.tables['job_categories']
            
            # Total job types (count distinct types from jobs with filtered criteria)
            total_types = db.session.query(func.count(distinct(job_types.c.id))).join(
                job_job_types, job_types.c.id == job_job_types.c.job_type_id
            ).join(
                jobs, job_job_types.c.job_id == jobs.c.id
            ).filter(and_(*filters)).scalar()
            
            # Total categories (count distinct categories from jobs with filtered criteria)
            total_categories = db.session.query(func.count(distinct(job_categories.c.id))).join(
                jobs, job_categories.c.id == jobs.c.job_category_id
            ).filter(and_(*filters)).scalar()
            
            return jsonify({
                'totalJobs': total_jobs,
                'totalCompanies': total_companies,
                'totalTypes': total_types,
                'totalCategories': total_categories
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobsTrend')
    def get_jobs_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for jobs trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                func.date(jobs.c.date_posted)            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getSalaryTrend')
    def get_salary_trend():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.min_salary.isnot(None),
                jobs.c.max_salary.isnot(None),
                jobs.c.min_salary > 0,
                jobs.c.max_salary > 0
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for salary data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                jobs.c.min_salary,
                jobs.c.max_salary
            ).filter(and_(*filters))
            
            results = query.all()
            
            if not results:
                return jsonify({
                    'dates': [],
                    'salaries': []
                })
            
            # Convert to pandas DataFrame for easier manipulation
            df = pd.DataFrame([(r.date, r.min_salary, r.max_salary) for r in results], 
                            columns=['date', 'min_salary', 'max_salary'])
            
            # Calculate average salary for each job
            df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
              # Group by date and calculate daily median
            daily_median = df.groupby('date')['avg_salary'].median().reset_index()
            daily_median = daily_median.sort_values('date')
            
            dates = [date.strftime('%Y-%m-%d') for date in daily_median['date']]
            salaries = [round(float(salary), 2) for salary in daily_median['avg_salary']]
            
            return jsonify({
                'dates': dates,
                'salaries': salaries
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getTopStates')
    def get_top_states():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = int(request.args.get('limit', 5))
            
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for top states
            query = db.session.query(
                jobs.c.state.label('state'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                jobs.c.state
            ).order_by(func.count(jobs.c.id).desc()).limit(limit)
            
            results = query.all()
            
            states = [result.state for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'states': states,
                'counts': counts        })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getTopCategories')
    def get_top_categories():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = int(request.args.get('limit', 5))
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Get job_categories table reference
            job_categories = db.metadata.tables['job_categories']
            
            # Query for top categories
            query = db.session.query(
                job_categories.c.name.label('category'),
                func.count(jobs.c.id).label('count')
            ).join(
                job_categories, jobs.c.job_category_id == job_categories.c.id
            ).filter(and_(*filters)).group_by(
                job_categories.c.name
            ).order_by(func.count(jobs.c.id).desc()).limit(limit)
            
            results = query.all()
            
            categories = [result.category for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'categories': categories,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getStates')
    def get_states():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
              # Query for all states
            query = db.session.query(
                jobs.c.state.distinct().label('state')
            ).filter(and_(*filters)).order_by(jobs.c.state)
            
            results = query.all()
            states = [result.state for result in results if result.state]
            
            return jsonify({'states': states})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getLocationStats')
    def get_location_stats():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_state = request.args.get('state')
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            if selected_state:
                filters.append(jobs.c.state == selected_state)
            
            # Total jobs
            total_jobs = db.session.query(func.count(jobs.c.id)).filter(and_(*filters)).scalar()
            
            # Calculate average salary using pandas
            salary_query = db.session.query(
                jobs.c.min_salary,
                jobs.c.max_salary            ).filter(
                and_(*filters), 
                jobs.c.min_salary.isnot(None), 
                jobs.c.max_salary.isnot(None), 
                jobs.c.min_salary > 0, 
                jobs.c.max_salary > 0
            )
            
            salary_results = salary_query.all()
            avg_salary = None
            
            if salary_results:
                df = pd.DataFrame([(r.min_salary, r.max_salary) for r in salary_results], 
                                columns=['min_salary', 'max_salary'])
                df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
                avg_salary = round(float(df['avg_salary'].median()), 2)
            
            # Total companies
            total_companies = db.session.query(func.count(distinct(jobs.c.company_name))).filter(and_(*filters)).scalar()
            
            # Total states (only if not filtering by specific state)
            if selected_state:
                total_states = 1
            else:
                total_states = db.session.query(func.count(distinct(jobs.c.state))).filter(
                    and_(*filters), jobs.c.state.isnot(None)
                ).scalar()
            
            return jsonify({
                'totalJobs': total_jobs,
                'avgSalary': avg_salary,
                'totalCompanies': total_companies,
                'totalStates': total_states
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobsByState')
    def get_jobs_by_state():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = int(request.args.get('limit', 10))
            
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for jobs by state
            query = db.session.query(
                jobs.c.state.label('state'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                jobs.c.state
            ).order_by(func.count(jobs.c.id).desc()).limit(limit)
            
            results = query.all()
            
            states = [result.state for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'states': states,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getLocationTrend')
    def get_location_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_state = request.args.get('state')
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            if selected_state:
                filters.append(jobs.c.state == selected_state)
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getSalaryByState')
    def get_salary_by_state():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = int(request.args.get('limit', 10))
            
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None),
                jobs.c.min_salary.isnot(None),
                jobs.c.max_salary.isnot(None),
                jobs.c.min_salary > 0,
                jobs.c.max_salary > 0
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for salary data by state using pandas for median calculation
            query = db.session.query(
                jobs.c.state,
                jobs.c.min_salary,
                jobs.c.max_salary
            ).filter(and_(*filters))
            
            results = query.all()
            
            if not results:
                return jsonify({
                    'states': [],
                    'salaries': []
                })
            
            # Convert to pandas DataFrame and calculate median salary by state
            df = pd.DataFrame([(r.state, r.min_salary, r.max_salary) for r in results], 
                            columns=['state', 'min_salary', 'max_salary'])
            df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
              # Group by state and calculate median salary and job count
            state_stats = df.groupby('state').agg({
                'avg_salary': 'median',
                'state': 'count'  # Count of jobs per state
            }).rename(columns={'state': 'job_count'}).reset_index()
            state_stats = state_stats.sort_values('avg_salary', ascending=False).head(limit)
            
            states = list(state_stats['state'])
            salaries = [round(float(salary), 2) for salary in state_stats['avg_salary']]
            job_counts = [int(count) for count in state_stats['job_count']]
            
            return jsonify({
                'states': states,
                'salaries': salaries,
                'jobCounts': job_counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getStateCategoryData')
    def get_state_category_data():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_state = request.args.get('state')
            limit = int(request.args.get('limit', 5))
              # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            if selected_state:
                filters.append(jobs.c.state == selected_state)
            
            # Get job_categories table reference
            job_categories = db.metadata.tables['job_categories']
            
            # Query for categories in selected state/all states
            query = db.session.query(
                job_categories.c.name.label('category'),
                func.count(jobs.c.id).label('count')
            ).join(
                job_categories, jobs.c.job_category_id == job_categories.c.id
            ).filter(and_(*filters)).group_by(
                job_categories.c.name
            ).order_by(func.count(jobs.c.id).desc()).limit(limit)
            
            results = query.all()
            
            categories = [result.category for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'categories': categories,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getCategories')
    def get_categories():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Get job_categories table reference
            job_categories = db.metadata.tables['job_categories']
              # Query for all categories
            query = db.session.query(
                job_categories.c.id.label('id'),
                job_categories.c.name.label('name')
            ).join(
                jobs, job_categories.c.id == jobs.c.job_category_id
            ).filter(and_(*filters)).distinct().order_by(job_categories.c.name)
            
            results = query.all()
            categories = [{'id': result.id, 'name': result.name} for result in results if result.name]
            
            return jsonify({'categories': categories})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getCategoryStats')
    @app.route('/api/getCategoryStats')
    def get_category_stats():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_category = request.args.get('category')
            
            # Build query filters  
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Get job_categories table reference
            job_categories = db.metadata.tables['job_categories']
            
            if selected_category:
                # Join with job_categories to filter by category name
                filters.append(job_categories.c.name == selected_category)
                category_join = [job_categories, jobs.c.job_category_id == job_categories.c.id]
            else:
                category_join = []
            
            # Build base query with optional category join
            base_query = db.session.query(jobs.c.id)
            if category_join:
                base_query = base_query.join(*category_join)
            
            # Total jobs
            total_jobs = base_query.filter(and_(*filters)).count()
            
            # Calculate median salary using pandas
            salary_query = base_query.filter(
                and_(*filters), jobs.c.min_salary.isnot(None), jobs.c.max_salary.isnot(None),
                jobs.c.min_salary > 0, jobs.c.max_salary > 0
            )
            
            # Get salary data for median calculation
            salary_data_query = db.session.query(
                jobs.c.min_salary,
                jobs.c.max_salary
            ).filter(
                jobs.c.id.in_(salary_query.subquery())
            )
            
            salary_results = salary_data_query.all()
            avg_salary = None
            
            if salary_results:
                df = pd.DataFrame([(r.min_salary, r.max_salary) for r in salary_results], 
                                columns=['min_salary', 'max_salary'])
                df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
                avg_salary = round(float(df['avg_salary'].median()), 2)
            
            # Total companies
            company_query = base_query.filter(and_(*filters))
            total_companies = company_query.with_entities(func.count(distinct(jobs.c.company_name))).scalar()
            
            # Total categories (only if not filtering by specific category)
            if selected_category:
                total_categories = 1
            else:
                total_categories = db.session.query(func.count(distinct(job_categories.c.id))).join(
                    jobs, job_categories.c.id == jobs.c.job_category_id
                ).filter(and_(*filters)).scalar()
            
            return jsonify({
                'totalJobs': total_jobs,
                'avgSalary': avg_salary,
                'totalCompanies': total_companies,
                'totalCategories': total_categories
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobsByCategory')
    def get_jobs_by_category():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            # Remove limit for full table/chart
            # limit = int(request.args.get('limit', 10))
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # Get job_categories table reference
            job_categories = db.metadata.tables['job_categories']
            # Query for jobs by category
            query = db.session.query(
                job_categories.c.name.label('category'),
                func.count(jobs.c.id).label('count')
            ).join(
                job_categories, jobs.c.job_category_id == job_categories.c.id
            ).filter(and_(*filters)).group_by(
                job_categories.c.name
            ).order_by(func.count(jobs.c.id).desc())
            # No .limit()
            results = query.all()
            categories = [result.category for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'categories': categories,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getCategoryTrend')
    def get_category_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_category = request.args.get('category')
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Get job_categories table reference and add category filter if needed
            if selected_category:
                job_categories = db.metadata.tables['job_categories']
                
                # Query for trend data with category filter
                query = db.session.query(
                    func.date(jobs.c.date_posted).label('date'),
                    func.count(jobs.c.id).label('count')
                ).join(
                    job_categories, jobs.c.job_category_id == job_categories.c.id
                ).filter(
                    and_(*filters), job_categories.c.name == selected_category
                ).group_by(
                    func.date(jobs.c.date_posted)
                ).order_by(func.date(jobs.c.date_posted))
            else:
                # Query for trend data without category filter
                query = db.session.query(
                    func.date(jobs.c.date_posted).label('date'),
                    func.count(jobs.c.id).label('count')
                ).filter(and_(*filters)).group_by(
                    func.date(jobs.c.date_posted)
                ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getSalaryByCategory')
    def get_salary_by_category():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', None)
            if limit is not None:
                try:
                    limit = int(limit)
                except Exception:
                    limit = None
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.min_salary.isnot(None),
                jobs.c.max_salary.isnot(None),
                jobs.c.min_salary > 0,
                jobs.c.max_salary > 0
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # Get job_categories table reference
            job_categories = db.metadata.tables['job_categories']
            # Query for salary data by category using pandas for median calculation
            query = db.session.query(
                job_categories.c.name,
                jobs.c.min_salary,
                jobs.c.max_salary
            ).join(
                job_categories, jobs.c.job_category_id == job_categories.c.id
            ).filter(and_(*filters))
            results = query.all()
            if not results:
                return jsonify({
                    'categories': [],
                    'salaries': [],
                    'jobCounts': []
                })
            # Convert to pandas DataFrame and calculate median salary by category
            df = pd.DataFrame([(r.name, r.min_salary, r.max_salary) for r in results], 
                            columns=['category', 'min_salary', 'max_salary'])
            df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
            # Group by category and calculate median salary and job count
            grouped = df.groupby('category').agg(
                median_salary=('avg_salary', 'median'),
                job_count=('avg_salary', 'count')
            ).reset_index()
            grouped = grouped.sort_values('median_salary', ascending=False)
            if limit:
                grouped = grouped.head(limit)
            categories = list(grouped['category'])
            salaries = [round(float(s), 2) for s in grouped['median_salary']]
            job_counts = [int(c) for c in grouped['job_count']]
            return jsonify({
                'categories': categories,
                'salaries': salaries,
                'jobCounts': job_counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobsBySkill')
    def get_jobs_by_skill():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = int(request.args.get('limit', 10))
            
            # Get table references
            job_skills = db.metadata.tables['job_skills']
            skills = db.metadata.tables['skills']
            
            # Build query filters for jobs
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for skills with job counts
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(and_(*filters)).group_by(
                skills.c.skill_name
            ).order_by(func.count(distinct(jobs.c.id)).desc()).limit(limit)
            
            results = query.all()
            
            skill_names = [result.skill for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'skills': skill_names,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getSkillTrend')
    def get_skill_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_skill = request.args.get('skill')
            
            # Get table references
            job_skills = db.metadata.tables['job_skills']
            skills = db.metadata.tables['skills']
            
            # Build query filters for jobs
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # If skill is selected, add skill filter
            if selected_skill:
                skill_job_ids = db.session.query(job_skills.c.job_id).join(
                    skills, job_skills.c.skill_id == skills.c.id
                ).filter(skills.c.skill_name == selected_skill).subquery()
                
                filters.append(jobs.c.id.in_(skill_job_ids))
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/getSalaryBySkill')
    def get_salary_by_skill():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = int(request.args.get('limit', 10))
            
            # Get table references
            job_skills = db.metadata.tables['job_skills']
            skills = db.metadata.tables['skills']
            
            # Build query filters for jobs
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.min_salary.isnot(None),
                jobs.c.max_salary.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for salary data by skill using pandas for median calculation
            query = db.session.query(
                skills.c.skill_name,
                jobs.c.min_salary,
                jobs.c.max_salary
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(and_(*filters))
            
            results = query.all()
            
            if not results:
                return jsonify({
                    'skills': [],
                    'salaries': []
                })
            
            # Convert to pandas DataFrame and calculate median salary by skill
            df = pd.DataFrame([(r.skill_name, r.min_salary, r.max_salary) for r in results], 
                            columns=['skill', 'min_salary', 'max_salary'])
            df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
            
            # Group by skill and calculate median salary
            skill_median = df.groupby('skill')['avg_salary'].median().reset_index()
            skill_median = skill_median.sort_values('avg_salary', ascending=False).head(limit)
            
            skill_names = list(skill_median['skill'])
            salaries = [round(float(salary), 2) for salary in skill_median['avg_salary']]
            
            return jsonify({
                'skills': skill_names,
                'salaries': salaries
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getSkillStateData')
    def get_skill_state_data():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_skill = request.args.get('skill')
            limit = int(request.args.get('limit', 5))
            
            # Get table references
            job_skills = db.metadata.tables['job_skills']
            skills = db.metadata.tables['skills']
            
            # Build query filters for jobs
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
                
            # If skill is selected, add skill filter
            if selected_skill:
                skill_job_ids = db.session.query(job_skills.c.job_id).join(
                    skills, job_skills.c.skill_id == skills.c.id
                ).filter(skills.c.skill_name == selected_skill).subquery()
                
                filters.append(jobs.c.id.in_(skill_job_ids))
            
            # Query for states with skill jobs
            query = db.session.query(
                jobs.c.state.label('state'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                jobs.c.state
            ).order_by(func.count(jobs.c.id).desc()).limit(limit)
            
            results = query.all()
            
            states = [result.state for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'states': states,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Job Types API endpoints
    @app.route('/api/getJobTypes')
    def get_job_types():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            
            # Build query filters for jobs
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
              # Query for all job types that have associated jobs in the date range
            query = db.session.query(
                job_types.c.type_name.distinct().label('type')
            ).join(
                job_job_types, job_types.c.id == job_job_types.c.job_type_id
            ).join(
                jobs, job_job_types.c.job_id == jobs.c.id
            ).filter(and_(*filters)).order_by(job_types.c.type_name)
            
            results = query.all()
            type_list = [result.type for result in results if result.type]
            
            return jsonify({'types': type_list})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobTypeStats')
    def get_job_type_stats():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_type = request.args.get('type')
            
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            
            # Build query filters for jobs
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # If type is selected, add type filter
            if selected_type:
                # Get jobs with this specific type
                type_job_ids = db.session.query(job_job_types.c.job_id).join(
                    job_types, job_job_types.c.job_type_id == job_types.c.id
                ).filter(job_types.c.type_name == selected_type).subquery()
                
                filters.append(jobs.c.id.in_(type_job_ids))
            
            # Total jobs
            total_jobs = db.session.query(func.count(jobs.c.id)).filter(and_(*filters)).scalar()
            
            # Calculate median salary using pandas
            salary_query = db.session.query(
                jobs.c.min_salary,
                jobs.c.max_salary
            ).filter(
                and_(*filters), jobs.c.min_salary.isnot(None), jobs.c.max_salary.isnot(None),
                jobs.c.min_salary > 0, jobs.c.max_salary > 0
            )
            
            salary_results = salary_query.all()
            avg_salary = None
            
            if salary_results:
                df = pd.DataFrame([(r.min_salary, r.max_salary) for r in salary_results], 
                                columns=['min_salary', 'max_salary'])
                df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
                avg_salary = round(float(df['avg_salary'].median()), 2)
            
            # Total companies
            total_companies = db.session.query(func.count(distinct(jobs.c.company_name))).filter(and_(*filters)).scalar()
            
            # Total job types 
            if selected_type:
                total_types = 1
            else:
                total_types = db.session.query(func.count(distinct(job_types.c.id))).join(
                    job_job_types, job_types.c.id == job_job_types.c.job_type_id
                ).join(
                    jobs, job_job_types.c.job_id == jobs.c.id
                ).filter(and_(*[f for f in filters if 'job_id' not in str(f)])).scalar()
                
            return jsonify({
                'totalJobs': total_jobs,
                'avgSalary': avg_salary,
                'totalCompanies': total_companies,
                'totalTypes': total_types
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/getJobsByType')
    def get_jobs_by_type():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', None)
            if limit is not None:
                try:
                    limit = int(limit)
                except Exception:
                    limit = None
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # Query for job types with job counts
            query = db.session.query(
                job_types.c.type_name.label('type'),
                func.count(jobs.c.id).label('count')
            ).join(
                job_job_types, job_types.c.id == job_job_types.c.job_type_id
            ).join(
                jobs, job_job_types.c.job_id == jobs.c.id
            ).filter(and_(*filters)).group_by(
                job_types.c.type_name
            ).order_by(func.count(jobs.c.id).desc())
            if limit:
                query = query.limit(limit)
            results = query.all()
            types = [result.type for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'types': types,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/getJobTypeTrend')
    def get_job_type_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_type = request.args.get('type')
            
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # If type is selected, add type filter
            if selected_type:
                type_job_ids = db.session.query(job_job_types.c.job_id).join(
                    job_types, job_job_types.c.job_type_id == job_types.c.id
                ).filter(job_types.c.type_name == selected_type).subquery()
                
                filters.append(jobs.c.id.in_(type_job_ids))
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/getSalaryByType')
    def get_salary_by_type():
        try:
            import pandas as pd
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', None)
            if limit is not None:
                try:
                    limit = int(limit)
                except Exception:
                    limit = None
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.min_salary.isnot(None),
                jobs.c.max_salary.isnot(None),
                jobs.c.min_salary > 0,
                jobs.c.max_salary > 0
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # Query for salary data by job type
            query = db.session.query(
                job_types.c.type_name,
                jobs.c.min_salary,
                jobs.c.max_salary
            ).join(
                job_job_types, job_types.c.id == job_job_types.c.job_type_id
            ).join(
                jobs, job_job_types.c.job_id == jobs.c.id
            ).filter(and_(*filters))
            results = query.all()
            if not results:
                return jsonify({
                    'types': [],
                    'salaries': [],
                    'counts': []
                })
            # Convert to pandas DataFrame for median calculation
            df = pd.DataFrame([(r.type_name, r.min_salary, r.max_salary) for r in results], 
                            columns=['type', 'min_salary', 'max_salary'])
            df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
            # Group by type and calculate median salary and job count
            grouped = df.groupby('type').agg(
                median_salary=('avg_salary', 'median'),
                job_count=('avg_salary', 'count')
            ).reset_index()
            grouped = grouped.sort_values('median_salary', ascending=False)
            if limit:
                grouped = grouped.head(limit)
            types = list(grouped['type'])
            salaries = [round(float(s), 2) for s in grouped['median_salary']]
            job_counts = [int(c) for c in grouped['job_count']]
            return jsonify({
                'types': types,
                'salaries': salaries,
                'counts': job_counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobTypeStateData')
    def get_job_type_state_data():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_type = request.args.get('type')
            limit = request.args.get('limit', None)
            if limit is not None:
                try:
                    limit = int(limit)
                except Exception:
                    limit = None
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # If type is selected, add type filter
            if selected_type:
                type_job_ids = db.session.query(job_job_types.c.job_id).join(
                    job_types, job_job_types.c.job_type_id == job_types.c.id
                ).filter(job_types.c.type_name == selected_type).subquery()
                
                filters.append(jobs.c.id.in_(type_job_ids))
            
            # Query for state distribution
            query = db.session.query(
                jobs.c.state.label('state'),
                func.count(jobs.c.id).label('count')
            ).filter(and_(*filters)).group_by(
                jobs.c.state
            ).order_by(func.count(jobs.c.id).desc())
            if limit:
                query = query.limit(limit)
            results = query.all()
            
            states = [result.state for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'states': states,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/getCategoryStateData')
    def get_category_state_data():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_category = request.args.get('category')
            limit = request.args.get('limit', None)
            if limit is not None:
                try:
                    limit = int(limit)
                except Exception:
                    limit = None
            # Build query filters
            filters = [
                jobs.c.source.in_(['jobstreet','ricebowl']),
                jobs.c.state.isnot(None)
            ]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # Get job_categories table reference and add category filter if needed
            if selected_category:
                job_categories = db.metadata.tables['job_categories']
                query = db.session.query(
                    jobs.c.state.label('state'),
                    func.count(jobs.c.id).label('count')
                ).join(
                    job_categories, jobs.c.job_category_id == job_categories.c.id
                ).filter(
                    and_(*filters), job_categories.c.name == selected_category
                ).group_by(
                    jobs.c.state
                ).order_by(func.count(jobs.c.id).desc())
            else:
                query = db.session.query(
                    jobs.c.state.label('state'),
                    func.count(jobs.c.id).label('count')
                ).filter(and_(*filters)).group_by(
                    jobs.c.state
                ).order_by(func.count(jobs.c.id).desc())
            if limit:
                query = query.limit(limit)
            results = query.all()
            states = [result.state for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'states': states,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getJobTypeCategoryData')
    def get_job_type_category_data():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            selected_type = request.args.get('type')
            limit = request.args.get('limit', None)
            if limit is not None:
                try:
                    limit = int(limit)
                except Exception:
                    limit = None
            # Get table references
            job_job_types = db.metadata.tables['job_job_types']
            job_types = db.metadata.tables['job_types']
            job_categories = db.metadata.tables['job_categories']
            # Build query filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            # If type is selected, filter jobs by type
            if selected_type:
                type_job_ids = db.session.query(job_job_types.c.job_id).join(
                    job_types, job_job_types.c.job_type_id == job_types.c.id
                ).filter(job_types.c.type_name == selected_type).subquery()
                filters.append(jobs.c.id.in_(type_job_ids))
            # Query for categories with job counts
            query = db.session.query(
                job_categories.c.name.label('category'),
                func.count(jobs.c.id).label('count')
            ).join(
                jobs, job_categories.c.id == jobs.c.job_category_id
            ).filter(and_(*filters)).group_by(
                job_categories.c.name
            ).order_by(func.count(jobs.c.id).desc())
            if limit:
                query = query.limit(limit)
            results = query.all()
            categories = [result.category for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'categories': categories,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # =======================================================
    # SKILL ENDPOINTS 
    # =======================================================
    
    # Language Endpoints
    @app.route('/api/getLanguageTrend')
    def get_language_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            skill = request.args.get('skill')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build base filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Language skill filter
            skill_filters = [skills.c.is_language == True]
            if skill:
                skill_filters.append(skills.c.skill_name == skill)
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, jobs.c.id == job_skills.c.job_id
            ).join(
                skills, job_skills.c.skill_id == skills.c.id
            ).filter(
                and_(*filters),
                and_(*skill_filters)
            ).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getTopLanguages')
    def get_top_languages():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', 5)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for top languages
            query = db.session.query(
                skills.c.skill_name.label('language'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_language == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            
            results = query.all()
            languages = [result.language for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'languages': languages,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getAllLanguages')
    def get_all_languages():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for all languages with job counts > 0
            query = db.session.query(
                skills.c.skill_name.label('language'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_language == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            )
            
            results = query.all()
            languages = [result.language for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'languages': languages,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Soft Skills Endpoints
    @app.route('/api/getSoftSkillTrend')
    def get_soft_skill_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            skill = request.args.get('skill')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build base filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Soft skill filter
            skill_filters = [skills.c.is_soft_skill == True]
            if skill:
                skill_filters.append(skills.c.skill_name == skill)
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, jobs.c.id == job_skills.c.job_id
            ).join(
                skills, job_skills.c.skill_id == skills.c.id
            ).filter(
                and_(*filters),
                and_(*skill_filters)
            ).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getTopSoftSkills')
    def get_top_soft_skills():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', 10)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for top soft skills
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_soft_skill == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getAllSoftSkills')
    def get_all_soft_skills():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for all soft skills with job counts > 0
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_soft_skill == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            )
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            return jsonify({
                'skills': skills_list,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getSoftSkillsByCategory')
    def get_soft_skills_by_category():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            category = request.args.get('category')
            limit = request.args.get('limit', 50)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            job_categories = db.metadata.tables['job_categories']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Add category filter if specified
            if category:
                filters.append(job_categories.c.id == category)
            
            # Query for soft skills by category
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            )
            
            # Join categories if needed
            if category:
                query = query.join(job_categories, jobs.c.job_category_id == job_categories.c.id)
            
            query = query.filter(
                and_(*filters),
                skills.c.is_soft_skill == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            # Get category name if category ID is provided
            category_name = 'All Categories'
            if category:
                category_query = db.session.query(job_categories.c.name).filter(job_categories.c.id == category).first()
                if category_query:
                    category_name = category_query[0]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts,
                'category': category_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Hard Skills Endpoints
    @app.route('/api/getHardSkillTrend')
    def get_hard_skill_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            skill = request.args.get('skill')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build base filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Hard skill filter
            skill_filters = [skills.c.is_hard_skill == True]
            if skill:
                skill_filters.append(skills.c.skill_name == skill)
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, jobs.c.id == job_skills.c.job_id
            ).join(
                skills, job_skills.c.skill_id == skills.c.id
            ).filter(
                and_(*filters),
                and_(*skill_filters)
            ).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getTopHardSkills')
    def get_top_hard_skills():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', 10)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for top hard skills
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_hard_skill == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getAllHardSkills')
    def get_all_hard_skills():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for all hard skills with job counts > 0
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_hard_skill == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            )
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getHardSkillsByCategory')
    def get_hard_skills_by_category():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            category = request.args.get('category')
            limit = request.args.get('limit', 50)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            job_categories = db.metadata.tables['job_categories']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Add category filter if specified
            if category:
                filters.append(job_categories.c.id == category)
            
            # Query for hard skills by category
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            )
            
            # Join categories if needed
            if category:
                query = query.join(job_categories, jobs.c.job_category_id == job_categories.c.id)
            
            query = query.filter(
                and_(*filters),
                skills.c.is_hard_skill == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            # Get category name if category ID is provided
            category_name = 'All Categories'
            if category:
                category_query = db.session.query(job_categories.c.name).filter(job_categories.c.id == category).first()
                if category_query:
                    category_name = category_query[0]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts,
                'category': category_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Certification Endpoints
    @app.route('/api/getCertificationTrend')
    def get_certification_trend():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            skill = request.args.get('skill')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build base filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Certification filter
            skill_filters = [skills.c.is_certification == True]
            if skill:
                skill_filters.append(skills.c.skill_name == skill)
            
            # Query for trend data
            query = db.session.query(
                func.date(jobs.c.date_posted).label('date'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, jobs.c.id == job_skills.c.job_id
            ).join(
                skills, job_skills.c.skill_id == skills.c.id
            ).filter(
                and_(*filters),
                and_(*skill_filters)
            ).group_by(
                func.date(jobs.c.date_posted)
            ).order_by(func.date(jobs.c.date_posted))
            
            results = query.all()
            dates = [result.date.strftime('%Y-%m-%d') for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'dates': dates,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getTopCertifications')
    def get_top_certifications():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            limit = request.args.get('limit', 10)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for top certifications
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
           
            ).filter(
                and_(*filters),
                skills.c.is_certification == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getAllCertifications')
    def get_all_certifications():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Query for all certifications with job counts > 0
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            ).filter(
                and_(*filters),
                skills.c.is_certification == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            )
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/getCertificationsByCategory')
    def get_certifications_by_category():
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            category = request.args.get('category')
            limit = request.args.get('limit', 50)
            
            # Get table references
            skills = db.metadata.tables['skills']
            job_skills = db.metadata.tables['job_skills']
            job_categories = db.metadata.tables['job_categories']
            
            # Build filters
            filters = [jobs.c.source.in_(['jobstreet','ricebowl'])]
            if start_date:
                filters.append(func.date(jobs.c.date_posted) >= start_date)
            if end_date:
                filters.append(func.date(jobs.c.date_posted) <= end_date)
            
            # Add category filter if specified
            if category:
                filters.append(job_categories.c.id == category)
            
            # Query for certifications by category
            query = db.session.query(
                skills.c.skill_name.label('skill'),
                func.count(distinct(jobs.c.id)).label('count')
            ).join(
                job_skills, skills.c.id == job_skills.c.skill_id
            ).join(
                jobs, job_skills.c.job_id == jobs.c.id
            )
            
            # Join categories if needed
            if category:
                query = query.join(job_categories, jobs.c.job_category_id == job_categories.c.id)
            
            query = query.filter(
                and_(*filters),
                skills.c.is_certification == True
            ).group_by(
                skills.c.skill_name
            ).having(
                func.count(distinct(jobs.c.id)) > 0
            ).order_by(
                func.count(distinct(jobs.c.id)).desc()
            ).limit(int(limit))
            
            results = query.all()
            skills_list = [result.skill for result in results]
            counts = [result.count for result in results]
            
            # Get category name if category ID is provided
            category_name = 'All Categories'
            if category:
                category_query = db.session.query(job_categories.c.name).filter(job_categories.c.id == category).first()
                if category_query:
                    category_name = category_query[0]
            
            return jsonify({
                'skills': skills_list,
                'counts': counts,
                'category': category_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500