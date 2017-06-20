 # -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, flash
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_moment import Moment
from wtforms import IntegerField, SelectField, StringField, DateTimeField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import Required, Length, Regexp

from random import randint, sample, shuffle
from datetime import datetime
from threading import Timer
import json, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


class IndexForm(FlaskForm):
    randtype = SelectField(u'抽签类型', coerce=int, choices = \
    [(0, u'抛硬币'), (1, u'掷骰子'), (2, u'选数字'), (3, u'比赛分组'), (4, u'从一个列表中抽取若干项')])
    submit = SubmitField(u'提交')

class RandomForm(FlaskForm):
    sched = DateTimeField(u'请输入抽取的时间（格式为 YYYY-mm-dd HH:MM:SS，例如 2017-03-29 21:30）：', validators=[Required()])
    description = StringField(u'输入描述：', validators=[Required()])
    url = StringField(u'URL（例如您输入的是 DEMO，将会生成一个http://drawlots.online/verify/id/DEMO的检验链接）：', \
        validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, u'URL只能由字母，数字，英文句点和下划线组成')])
    submit = SubmitField(u'提交')

class CoinForm(RandomForm):
    num = IntegerField(u'请输入硬币数:', validators=[Required()])


class DiceForm(RandomForm):
    num = IntegerField(u'请输入骰子数:', validators=[Required()])


class NumberForm(RandomForm):
    start = IntegerField(u'开始于:', validators=[Required()])
    end = IntegerField(u'结束于:', validators=[Required()])
    num = IntegerField(u'选取的数字个数:', validators=[Required()])
    distinct = BooleanField(u'是否允许重复？')


class TournamentForm(RandomForm):
    lines = TextAreaField(u'输入成员（每个一行）：', validators=[Required()])
    num = IntegerField(u'每个组的成员数：', validators=[Required()])


class PickForm(RandomForm):
    lines = TextAreaField(u'输入成员（每个一行）：', validators=[Required()])
    num = IntegerField(u'选取的成员数：', validators=[Required()])

class VerifyForm(FlaskForm):
    url = StringField(u'URL（如果您的检验链接是http://drawlots.online/verify/id/DEMO请直接输入 DEMO ）：', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          u'URL只能由字母，数字，英文句点和下划线组成')])
    submit = SubmitField(u'提交')

def coin_delay(data):
    data = json.loads(open('data/%s.json' % data['url'], 'r').read())
    data['result'] = [randint(0, 1) for i in range(data['num'])]
    data['done'] = True
    with open('data/%s.json' % data['url'], 'w') as json_file:
        json_file.write(json.dumps(data))

def dice_delay(data):
    data = json.loads(open('data/%s.json' % data['url'], 'r').read())
    data['result'] = [randint(1, 6) for i in range(data['num'])]
    data['done'] = True
    with open('data/%s.json' % data['url'], 'w') as json_file:
        json_file.write(json.dumps(data))

def num_delay(data):
    data = json.loads(open('data/%s.json' % data['url'], 'r').read())
    if not data['distinct']:
        data['result'] = sample(list(range(data['start'], data['end'])), data['num'])
    else:
        data['result'] = [randint(data['start'], data['end']) for i in range(data['num'])]
    data['done'] = True
    with open('data/%s.json' % data['url'], 'w') as json_file:
        json_file.write(json.dumps(data))

def tournament_delay(data):
    data = json.loads(open('data/%s.json' % data['url'], 'r').read())
    lines = data['lines']
    shuffle(lines)
    data['result'] = [lines[i : i + data['num']] for i in range(0, len(lines), data['num'])]
    data['done'] = True
    with open('data/%s.json' % data['url'], 'w') as json_file:
        json_file.write(json.dumps(data))

def pick_delay(data):
    data = json.loads(open('data/%s.json' % data['url'], 'r').read())
    lines = data['lines']
    data['result'] = sample(lines, data['num'])
    data['done'] = True
    with open('data/%s.json' % data['url'], 'w') as json_file:
        json_file.write(json.dumps(data))

@app.route('/', methods=['GET', 'POST'])
def index():
    form = IndexForm()
    if form.validate_on_submit():
        randtype = form.randtype.data
        TYPE_URL = {0:'coin', 1:'dice', 3:'num', 4:'pick'}
        return redirect(url_for(TYPE_URL[randtype]))
    return render_template('index.html', form=form)

@app.route('/coin', methods=['GET', 'POST'])
def coin():
    form = CoinForm()
    if form.validate_on_submit():
        randtype = 0
        date = datetime.now()
        sched = form.sched.data
        num = form.num.data
        description = form.description.data
        url = form.url.data
        done = False
        if os.path.exists('data/%s.json' % url):
            flash(u'URL"%s"已存在' % url, 'warning')
        else:
            data = {'randtype':randtype, 'date':date.strftime('%Y-%m-%d %H:%M:%S'), 'sched':sched.strftime('%Y-%m-%d %H:%M:%S'), 'num':num, 'description':description, 'done':False, 'url':url}
            with open('data/%s.json' % url, 'w') as json_file:
                json_file.write(json.dumps(data))
            coin_timer = Timer((sched - date).seconds, coin_delay, args=(data,))
            coin_timer.start()
            return redirect(url_for('success', url=url))
    return render_template('coin.html', form=form)

@app.route('/dice', methods=['GET', 'POST'])
def dice():
    form = DiceForm()
    if form.validate_on_submit():
        randtype = 1
        date = datetime.now()
        sched = form.sched.data
        num = form.num.data
        description = form.description.data
        url = form.url.data
        done = False
        if os.path.exists('data/%s.json' % url):
            flash(u'URL"%s"已存在' % url, 'warning')
        else:
            data = {'randtype':randtype, 'date':date.strftime('%Y-%m-%d %H:%M:%S'), 'sched':sched.strftime('%Y-%m-%d %H:%M:%S'), 'num':num, 'description':description, 'done':False, 'url':url}
            with open('data/%s.json' % url, 'w') as json_file:
                json_file.write(json.dumps(data))
            dice_timer = Timer((sched - date).seconds, dice_delay, args=(data,))
            dice_timer.start()
            return redirect(url_for('success', url=url))
    return render_template('dice.html', form=form)


@app.route('/num', methods=['GET', 'POST'])
def num():
    form = NumberForm()
    if form.validate_on_submit():
        randtype = 2
        date = datetime.now()
        sched = form.sched.data
        start = form.start.data
        end = form.end.data
        num = form.num.data
        distinct = form.distinct.data
        description = form.description.data
        url = form.url.data
        done = False
        if os.path.exists('data/%s.json' % url):
            flash(u'URL"%s"已存在' % url, 'warning')
        else:
            data = {'randtype':randtype, 'date':date.strftime('%Y-%m-%d %H:%M:%S'), 'sched':sched.strftime('%Y-%m-%d %H:%M:%S'), 'start':start, 'end':end, 'num':num, 'distinct':distinct, 'description':description, 'done':False, 'url':url}
            with open('data/%s.json' % url, 'w') as json_file:
                json_file.write(json.dumps(data))
            dice_timer = Timer((sched - date).seconds, num_delay, args=(data,))
            dice_timer.start()
            return redirect(url_for('success', url=url))
    return render_template('num.html', form=form)

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    form = TournamentForm()
    if form.validate_on_submit():
        randtype = 3
        date = datetime.now()
        sched = form.sched.data
        lines = form.lines.data.split()
        num = form.num.data
        description = form.description.data
        url = form.url.data
        done = False
        if os.path.exists('data/%s.json' % url):
            flash(u'URL"%s"已存在' % url, 'warning')
        else:
            data = {'randtype':randtype, 'date':date.strftime('%Y-%m-%d %H:%M:%S'), 'sched':sched.strftime('%Y-%m-%d %H:%M:%S'), 'lines':lines, 'num':num, 'description':description, 'done':False, 'url':url}
            with open('data/%s.json' % url, 'w') as json_file:
                json_file.write(json.dumps(data))
            dice_timer = Timer((sched - date).seconds, tournament_delay, args=(data,))
            dice_timer.start()
            return redirect(url_for('success', url=url))
    return render_template('tournament.html', form=form)


@app.route('/pick', methods=['GET', 'POST'])
def pick():
    form = PickForm()
    if form.validate_on_submit():
        randtype = 4
        date = datetime.now()
        sched = form.sched.data
        lines = form.lines.data.split()
        num = form.num.data
        description = form.description.data
        url = form.url.data
        done = False
        if os.path.exists('data/%s.json' % url):
            flash(u'URL"%s"已存在' % url, 'warning')
        else:
            data = {'randtype':randtype, 'date':date.strftime('%Y-%m-%d %H:%M:%S'), 'sched':sched.strftime('%Y-%m-%d %H:%M:%S'), 'lines':lines, 'num':num, 'description':description, 'done':False, 'url':url}
            with open('data/%s.json' % url, 'w') as json_file:
                json_file.write(json.dumps(data))
            dice_timer = Timer((sched - date).seconds, pick_delay, args=(data,))
            dice_timer.start()
            return redirect(url_for('success', url=url))
    return render_template('pick.html', form=form)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    form = VerifyForm()
    if form.validate_on_submit():
        url = form.url.data
        return redirect(url_for('verify_id', url=url))
    return render_template('verify/index.html', form=form)

@app.route('/verify/id/<url>')
def verify_id(url):
    if os.path.exists('data/%s.json' % url):
        data = json.loads(open('data/%s.json' % url, 'r').read())
        TYPE_URL = {0:'coin', 1:'dice', 2:'num', 3:'tournament', 4:'pick'}
        return render_template('verify/%s.html' % TYPE_URL[data['randtype']], data=data)
    return render_template('verify/404.html')

@app.route('/success/<url>')
def success(url):
    return render_template('success.html', url=url)

if __name__ == '__main__':
    manager.run()  