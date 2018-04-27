#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import hashlib

from conf import conf
from table import *
from sqlalchemy.sql import and_, or_, not_

def digest(word):
    m2 = hashlib.md5()
    line = '%s%s' % (word, conf.digest_salt)
    m2.update(line)
    token = m2.hexdigest()
    return token

def login_check(mobile=None, password=None):
    if not mobile or not password:
        return None
    s = DBSession()
    tok = digest(password)
    c = and_(JlyAdmin.mobile == mobile, JlyAdmin.password==tok)
    r = s.query(JlyAdmin).filter(c).first()
    if r:
        s.close()
        return r.dic_return()
    s.close()
    return None

def query_admin(uid=None):
    if not uid:
        return None
    uid = int(uid)
    s = DBSession()
    r = s.query(JlyAdmin).filter(JlyAdmin.id == uid).first()
    d = None if not r else r.dic_return()
    s.close()
    return d


def create_admin(name=None, mobile=None, password=None):
    if not name or not mobile or not password:
        return None
    s = DBSession()
    r = s.query(JlyAdmin).filter(JlyAdmin.mobile == mobile).first()
    if r:
        s.close()
        return None
    tok = digest(password)
    u = JlyAdmin(name=name, mobile=mobile, password=tok)
    s.add(u)
    s.commit()
    s.close()
    return True

def del_admin(uid=None):
    s = DBSession()
    r = s.query(JlyAdmin).filter(JlyAdmin.id == uid).delete(synchronize=False)
    s.commit()
    s.close()
    return True

def edit_admin(uid=None, name=None, password=None, mobile=None, state=None, s=None):
    if not uid:
        return None
    f = True
    D = {}
    if name:
        D[JlyAdmin.name] = name
    if password:
        tok = digest(password)
        D[JlyAdmin.password] = tok
    if mobile:
        D[JlyAdmin.mobile] = mobile
    if not state and state != 0 and state != '':
        pass
    else:
        state = int(state)
        if state in [0, 1]:
            D[JlyAdmin.valid_state] = state
    if D:
        f = s
        if not f:
            s = DBSession()
        s.query(JlyAdmin).filter(JlyAdmin.id == uid).update(D)
        s.commit()
    if not f:
        s.close()
    return True

def forbid_admin(uid=None):
    if not uid:
        return None
    r = edit_admin(uid=uid, state=1)
    return r

def allow_admin(uid=None):
    if not uid:
        return None
    r = edit_admin(uid=uid, state=0)
    return r

def list_admin(limit=None, page=None, next_=None):
    limit = int(limit) if limit else conf.admin_limit
    page  = int(page) if page else conf.admin_page
    next_ = int(next_) if next_ else 0
   
    s = DBSession()
    c = and_(JlyAdmin.role != 0)
    r = s.query(JlyAdmin).limit(limit).offset(page*next_)
    D = [e.dic_return() for e in r]
    s.close()
    return D


def edit_user(uid=None, opt=None, bc=None, state=0):
    if not uid:
        return False
    if not state and state != 0 and state != '':
        return False
    msg = ''
    if opt and int(opt) in [0,1,2,3,4]:
        msg = conf.reasons[opt]
    elif bc:
        msg = bc[:128]
    s = DBSession()
    r = s.query(User).filter(User.id == uid).first()
    if not r:
        s.close()
        return False
    if not state:
        if state != 0 or state != '':
            s.close()
            return False
    state = int(state)
    if state in [0, 1, 3]:
        r.state = state
        r.msg   = msg
        s.commit()
    s.close()
    return True 

def forbid_user(uid=None, opt=None, bc=None):
    r = edit_user(uid, opt, bc, 1)
    return r

def allow_user(uid=None, opt=None, bc=None):
    r = edit_user(uid, opt, bc, 3)
    return r

#num: rmb 分
def chongzhi(uid=None, num=None):
    if not uid or not num:
        return None
    s = DBSession()
    uid, num = int(uid), int(num)*100
    num = int(num/10) if not conf.price else int(num/conf.proce)
    ru = s.query(User).filter(User.id == uid).first()
    if ru:
        ra = s.query(User_accout).filter(User_accout.id == uid).first()
        if not ra:
            s.close()
            return None
        ra.num = ra.num + num
        s.commit()
    s.close()
    return True

def list_user(limit=None, page=None, next_=None):
    limit = int(limit) if limit else conf.user_limit
    page  = int(page) if page else conf.user_page
    next_ = int(next_) if next_ else 0

    s = DBSession()
    r = s.query(User).limit(limit).offset(page*next_)
    D = [e.dic_return() for e in r]
    s.close()
    return D

def list_zhenghun(limit=None, page=None, next_=None):
    limit = int(limit) if limit else conf.zhenghun_limit
    page  = int(page) if page else conf.zhenghun_page
    next_ = int(next_) if next_ else 0

    s = DBSession()
    r = s.query(Zhenghun).limit(limit).offset(page*next_)
    ids = [e.userid for e in r]
    u_m = {}
    if ids:
        ru = s.query(User).filter(User.id.in_(ids)).all()
        if ru:
            for e in ru:
                u_m[e.id] = e.dic_return()
    D = []
    for e in r:
        t = e.dic_return()
        if u_m.get(e.userid):
            t['valid_state'] = u_m[e.userid]['valid_state']
        else:
            t['valid_state'] = -1
        D.append(t)
    s.close()
    return D
#kind=0 zhenghun  kind=1 dating
def edit_tiezi(oid=None, opt=None, bc=None, state=0, kind=0):
    if not oid:
        return False
    if not state and state != 0 and state != '':
        return False
    msg = ''
    if opt and int(opt) in [0,1,2,3,4]:
        msg = conf.reasons[opt]
    elif bc:
        msg = bc[:128]
    s = DBSession()
    r = ''
    if kind == 0:
        r = s.query(Zhenghun).filter(Zhenghun.id == oid).first()
    else:
        r = s.query(Dating).filter(Dating.id == oid).first()

    if not r:
        s.close()
        return None 
    state = int(state)
    if state in [0,1,3]:
        r.state = state
        r.msg = msg
        s.commit()
    s.close()
    return True

def forbit_zhenghun(oid=None, opt=None, bc=None):
    r = edit_tiezi(oid, opt, bc, 1, 0)
    return r

def allow_zhenghun(oid=None, opt=None, bc=None):
    r = edit_tiezi(oid, opt, bc, 3, 0)
    return r

def del_zhenghun(oid=None, opt=None, bc=None):
    r = edit_tiezi(oid, opt, bc, 2, 0)
    return r

def list_dating(limit=None, page=None, next_=None):
    limit = int(limit) if limit else conf.dating_limit
    page  = int(page) if page else conf.dating_page
    next_ = int(next_) if next_ else 0

    s = DBSession()
    r = s.query(Dating).limit(limit).offset(page*next_)
    ids = [e.userid for e in r]
    u_m = {}
    if ids:
        ru = s.query(User).filter(User.id.in_(ids)).all()
        if ru:
            for e in ru:
                u_m[e.id] = e.dic_return()
    D = []
    for e in r:
        t = e.dic_return()
        if u_m.get(e.userid):
            t['valid_state'] = u_m[e.userid]['valid_state']
        else:
            t['valid_state'] = -1
        D.append(t)
    s.close()
    return D

def forbit_dating(oid=None, opt=None, bc=None):
    r = edit_tiezi(oid, opt, bc, 1, 1)
    return r

def allow_dating(oid=None, opt=None, bc=None):
    r = edit_tiezi(oid, opt, bc, 3, 1)
    return r

def del_dating(oid=None, opt=None, bc=None):
    r = edit_tiezi(oid, opt, bc, 2, 1)
    return r

def search_user(uid=None):
    if not uid:
        return None
    s = DBSession()
    r = s.query(User).filter(User.id == uid).first()
    D = r.dic_return() if r else {}
    s.close()
    return D

def search_zhenghun(zid=None):
    if not zid:
        return None
    s = DBSession()
    r = s.query(Zhenghun).filter(Zhenghun.id == zid).first()
    if not r:
        s.close()
        return None
    uid = r.userid
    ru = s.query(User).filter(User.id == uid).first()
    v_d = -1
    if ru:
        v_d = ru.valid_state
    d = r.dic_return()
    d['valid_state'] = v_d
    s.close()
    return d

def search_dating(did=None):
    if not did:
        return None
    s = DBSession()
    r = s.query(Dating).filter(Dating.id == did).first()
    if not r:
        s.close()
        return None
    uid = r.userid
    ru = s.query(User).filter(User.id == uid).first()
    v_d = -1
    if ru:
        v_d = ru.valid_state
    d = r.dic_return()
    d['valid_state'] = v_d
    s.close()
    return d


if __name__ == '__main__':
    r = list_user()
    print(r)
'''
    r = digest('jly2018!!!')
    print(r)
'''
