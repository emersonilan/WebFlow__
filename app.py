from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "segredo_super_secreto"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    deadline = db.Column(db.DateTime)
    pinned = db.Column(db.Boolean, default=False)  # 📌 NOVO

with app.app_context():
    db.drop_all()   # ⚠️ só execute uma vez se necessário
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            session['user_id'] = user.id
            return redirect('/')
        else:
            error = "Usuário ou senha incorretos"

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    order = request.args.get('order', 'default')

    query = Task.query.filter_by(user_id=session['user_id'])

    # 📌 PIN SEMPRE PRIMEIRO
    query = query.order_by(Task.pinned.desc())

    if order == 'date':
        query = query.order_by(Task.pinned.desc(), Task.deadline.asc())
    elif order == 'name':
        query = query.order_by(Task.pinned.desc(), Task.title.asc())
    elif order == 'done':
        query = query.order_by(Task.pinned.desc(), Task.done.asc())

    tasks = query.all()

    total = len(tasks)
    done = len([t for t in tasks if t.done])
    progress = int((done / total) * 100) if total > 0 else 0

    return render_template(
        'index.html',
        tasks=tasks,
        now=datetime.now(),
        order=order,
        progress=progress,
        total=total,
        done=done
    )

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    deadline = request.form.get('deadline')

    task = Task(
        title=request.form['title'],
        user_id=session['user_id'],
        deadline=datetime.strptime(deadline, "%Y-%m-%d") if deadline else None
    )

    db.session.add(task)
    db.session.commit()
    return redirect('/')

@app.route('/pin/<int:id>')
def pin(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)
    if task and task.user_id == session['user_id']:
        task.pinned = not task.pinned
        db.session.commit()

    return redirect('/')

@app.route('/done/<int:id>')
def done_task(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)
    if task and task.user_id == session['user_id']:
        task.done = not task.done
        db.session.commit()

    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)
    if task and task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()

    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)

    if not task or task.user_id != session['user_id']:
        return redirect('/')

    if request.method == 'POST':
        task.title = request.form['title']

        deadline = request.form.get('deadline')
        task.deadline = datetime.strptime(deadline, "%Y-%m-%d") if deadline else None

        db.session.commit()
        return redirect('/')

    return render_template('edit.html', task=task)

if __name__ == '__main__':
    app.run(debug=True)