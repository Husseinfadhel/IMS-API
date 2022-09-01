from fastapi import APIRouter
import requests
from tortoise.transactions import in_transaction

from models.models import Installments, States, Users, UserAuth, Students, StudentInstallments, TemporaryDelete, \
    TemporaryPatch, Branches, Governorates, Institutes, Posters

"""
Dear Programmer:
When I wrote this code, only god and I knew how it worked.
Now, only god knows it!
Therefore, if you are trying to optimize this routine and it fails (most surely),
please increase this counter as a warning for the next person:
total_hours_wasted_here = 48
"""
sync_router = APIRouter()

HOST = "http://65.20.73.107"


async def get_users() -> list:
    users = await Users.filter(sync_state=0).all()
    result_list = []
    for user in users:
        result_json = {"password": user.password, "username": user.username, "unique_id": user.unique_id,
                       "name": user.name}
        authority = []
        auth = await UserAuth.filter(user_id=user.id).prefetch_related('state').all()
        for au in auth:
            auth_json = {"state_unique_id": au.state.unique_id,
                         "unique_id": au.unique_id}
            authority.append(auth_json)
        result_json['authority'] = authority
        result_list.append(result_json)
    return result_list


async def get_del() -> dict:
    all_deleted = await TemporaryDelete.filter(sync_state=0).all()
    unique_id_students = []
    unique_id_students_install = []
    unique_id_states = []
    unique_id_users = []
    for deleted in all_deleted:
        if deleted.model_id == 1:
            unique_id_students.append(deleted.unique_id)
        elif deleted.model_id == 2:
            unique_id_states.append(deleted.unique_id)
        elif deleted.model_id == 3:
            unique_id_students_install.append(deleted.unique_id)
        elif deleted.model_id == 4:
            unique_id_users.append(deleted.unique_id)
        await TemporaryDelete.filter(id=deleted.id).update(sync_state=1)
    return {
        "unique_id_students": unique_id_students, "unique_id_students_install": unique_id_students_install,
        "unique_id_states": unique_id_states, "unique_id_users": unique_id_users
    }


async def get_edits() -> tuple:
    tp = await TemporaryPatch.filter(sync_state=0).all()
    students = []
    states = []
    student_installment = []
    users = []
    for item in tp:
        if item.model_id == 1:
            students.append(item.unique_id)
        if item.model_id == 2:
            states.append(item.unique_id)
        if item.model_id == 3:
            student_installment.append(item.unique_id)
        if item.model_id == 4:
            users.append(item.unique_id)

    return students, states, student_installment, users


def student_json(student) -> dict:
    branch_id = None
    if student.branch:
        branch_id = student.branch.id
    governorate_id = None
    if student.governorate:
        governorate_id = student.governorate.id
    institute_id = None
    if student.institute:
        institute_id = student.institute.id
    poster = None
    if student.poster:
        poster = student.poster.id
    return {"name": student.name, "school": student.school, "branch_id": branch_id,
            "governorate_id": governorate_id, "institute_id": institute_id,
            "state_unique_id": student.state.unique_id, "first_phone": student.first_phone,
            "second_phone": student.second_phone, "code_1": student.code_1, "code_2": student.code_2,
            "telegram_user": student.telegram_user,
            "created_at": str(student.created_at), "note": student.note,
            "total_amount": student.total_amount,
            "poster": poster, "remaining_amount": student.remaining_amount,
            "unique_id": student.unique_id}


async def get_all():
    branche_req = requests.get(f'{HOST}/branches')
    branches = await Branches.all().values('name')
    branches = [n['name'] for n in branches]
    branche_req = branche_req.json()
    branche_req = branche_req['branches']
    for branch in branche_req:
        if branch['name'] not in branches:
            async with in_transaction() as conn:
                new = Branches(id=branch['id'], name=branch['name'])
                await new.save(using_db=conn)
    governorates_req = requests.get(f'{HOST}/governorates')
    governorates = await Governorates.all().values('name')
    governorates = [n['name'] for n in governorates]
    governorates_req = governorates_req.json()
    governorates_req = governorates_req['governorates']
    for governorate in governorates_req:
        if governorate['name'] not in governorates:
            async with in_transaction() as conn:
                new = Governorates(
                    id=governorate['id'], name=governorate['name'])
                await new.save(using_db=conn)
    installments_req = requests.get(f'{HOST}/installments')
    installments = await Installments.all().values('unique_id')
    installments = [n['unique_id'] for n in installments]
    installments_req = installments_req.json()
    installments_req = installments_req['installments']
    for installment in installments_req:
        if installment['unique_id'] not in installments:
            async with in_transaction() as conn:
                new = Installments(id=installment['id'], name=installment['name'], unique_id=installment['unique_id'],
                                   sync_state=1)
                await new.save(using_db=conn)
    institutes_req = requests.get(f'{HOST}/institutes')
    institutes = await Institutes.all().values('name')
    institutes = [n['name'] for n in institutes]
    institutes_req = institutes_req.json()
    institutes_req = institutes_req['institutes']
    for institute in institutes_req:
        if institute['name'] not in institutes:
            async with in_transaction() as conn:
                new = Institutes(id=institute['id'], name=institute['name'])
                await new.save(using_db=conn)
    posters_req = requests.get(f'{HOST}/posters')
    posters = await Posters.all().values('name')
    posters = [n['name'] for n in posters]
    posters_req = posters_req.json()
    posters_req = posters_req['posters']
    for poster in posters_req:
        if poster['name'] not in posters:
            async with in_transaction() as conn:
                new = Posters(id=poster['id'], name=poster['name'])
                await new.save(using_db=conn)
    states_req = requests.get(f'{HOST}/states')
    states = await States.all().values('unique_id')
    states = [n['unique_id'] for n in states]
    states_req = states_req.json()
    states_req = states_req['states']
    for state in states_req:
        if state['unique_id'] in states and state['delete_state'] == 1:
            await States.filter(unique_id=state['unique_id']).delete()
        elif state['unique_id'] not in states and state['delete_state'] == 0:
            async with in_transaction() as conn:
                new = States(
                    name=state['name'], unique_id=state['unique_id'], sync_state=1)
                await new.save(using_db=conn)
        elif state['unique_id'] in states and state['delete_state'] == 0 and state['patch_state'] == 1:
            await States.filter(unique_id=state['unique_id']).update(name=state['name'])
    students_req = requests.get(f'{HOST}/students')
    students = await Students.all().values('unique_id')
    students = [n['unique_id'] for n in students]
    student_req = students_req.json()
    student_req = student_req['students']
    for student in student_req:
        if student['unique_id'] in students and student['delete_state'] == 1:
            await Students.filter(unique_id=student['unique_id']).delete()
        elif student['unique_id'] not in students and student['delete_state'] == 0:
            async with in_transaction() as conn:
                st = await States.filter(unique_id=student['_state']['unique_id']).first()
                new = Students(name=student['name'], school=student['school'], branch_id=student['branch_id'],
                               governorate_id=student['governorate_id'], institute_id=student['institute_id'],
                               state_id=st.id, first_phone=student['first_phone'],
                               second_phone=student['second_phone'], code_1=student['code_1'], code_2=student['code_2'],
                               telegram_user=student['telegram_user'], created_at=student['created_at'],
                               note=student['note'],
                               total_amount=student['total_amount'],
                               remaining_amount=student['remaining_amount'], poster_id=student['poster_id'],
                               unique_id=student['unique_id'], sync_state=1)
                await new.save(using_db=conn)
        elif student['unique_id'] in students and student['delete_state'] == 0 and student['patch_state'] == 1:
            st = await States.filter(unique_id=student['_state']['unique_id']).first()
            await Students.filter(unique_id=student['unique_id']).update(name=student['name'], school=student['school'],
                                                                         branch_id=student['branch_id'],
                                                                         governorate_id=student['governorate_id'],
                                                                         institute_id=student['institute_id'],
                                                                         state_id=st.id,
                                                                         first_phone=student['first_phone'],
                                                                         second_phone=student['second_phone'],
                                                                         code_1=student['code_1'],
                                                                         code_2=student['code_2'],
                                                                         telegram_user=student[
                                                                             'telegram_user'],
                                                                         created_at=student['created_at'],
                                                                         note=student['note'],
                                                                         total_amount=student['total_amount'],
                                                                         remaining_amount=student['remaining_amount'],
                                                                         poster_id=student['poster_id'],
                                                                         sync_state=1)
    users_auth_req = requests.get(f'{HOST}/users')
    users_auth_req = users_auth_req.json()
    users_auth_req = users_auth_req['users']
    users = await Users.all().values('unique_id')
    users = [n['unique_id'] for n in users]
    for user in users_auth_req:
        if user['unique_id'] in users and user['delete_state'] == 1:
            await Users.filter(unique_id=user['unique_id']).delete()
        elif user['unique_id'] not in users and user['delete_state'] == 0:
            async with in_transaction() as conn:
                new = Users(username=user['username'], password=user['password'], unique_id=user['unique_id'],
                            sync_state=1, name=user['name'])
                await new.save(using_db=conn)
                for auth in user['authority']:
                    if auth['delete_state'] != 1:
                        st_auth = await States.filter(unique_id=auth['state_unique_id']).first()
                        new2 = UserAuth(state_id=st_auth.id, user_id=new.id, unique_id=auth['auth_unique_id'],
                                        sync_state=0)
                        await new2.save(using_db=conn)

        elif user['unique_id'] in users and user['delete_state'] == 0 and user['patch_state'] == 1:
            await Users.filter(unique_id=user['unique_id']).update(sync_state=1, username=user['username'],
                                                                   password=user['password'], name=user['name'])
            get_user = await Users.filter(unique_id=user['unique_id']).first()
            for auth in user['authority']:
                if auth['delete_state'] != 1:
                    await UserAuth.filter(unique_id=auth['auth_unique_id']).delete()
                    async with in_transaction() as conn:
                        st_auth = await States.filter(unique_id=auth['state_unique_id']).first()
                        new2 = UserAuth(state_id=st_auth.id, user_id=get_user.id, unique_id=auth['auth_unique_id'],
                                        sync_state=0)
                        await new2.save(using_db=conn)
                if auth['delete_state'] == 1:
                    await UserAuth.filter(unique_id=auth['auth_unique_id']).delete()
    student_installments_req = requests.get(f'{HOST}/student_installment')
    student_installments = await StudentInstallments.all().values('unique_id')
    student_installments_req = student_installments_req.json()
    student_installments = [n['unique_id'] for n in student_installments]
    reqs = student_installments_req['students_installments']
    for req in reqs:
        if req['unique_id'] in student_installments and req['delete_state'] == 1:
            await StudentInstallments.filter(unique_id=req['unique_id']).delete()
        if req['unique_id'] not in student_installments and req['delete_state'] == 0:
            stu = await Students.filter(unique_id=req['_student']['unique_id']).first()
            install = await Installments.filter(unique_id=req['_installment']['unique_id']).first()
            if stu is not None:
                async with in_transaction() as conn:
                    new = StudentInstallments(unique_id=req['unique_id'], sync_state=1, invoice=req['invoice'],
                                              installment_id=install.id, student_id=stu.id, date=req['date'],
                                              amount=req['amount'])
                    await new.save(using_db=conn)
        if req['unique_id'] in student_installments and req['delete_state'] == 0 and req['patch_state'] == 1:
            stu = await Students.filter(unique_id=req['_student']['unique_id']).first()
            install = await Installments.filter(unique_id=req['_installment']['unique_id']).first()
            if stu is not None:
                await StudentInstallments.filter(unique_id=req['unique_id']).update(sync_state=1,
                                                                                    invoice=req['invoice'],
                                                                                    installment_id=install.id,
                                                                                    student_id=stu.id,
                                                                                    date=req['date'],
                                                                                    amount=req['amount'])


@sync_router.get('/sync')
async def sync():
    installments = await Installments.filter(sync_state=0).all()
    for install in installments:
        req = requests.post(f"{HOST}/installments",
                            json={"name": install.name, "unique_id": install.unique_id})
        if req.status_code == 200:
            await Installments.filter(id=install.id).update(sync_state=1)
    states = await States.filter(sync_state=0).all()
    for state in states:
        req = requests.post(f"{HOST}/state", json={"name": state.name,
                                                   "unique_id": state.unique_id})
        if req.status_code == 200:
            await States.filter(id=state.id).update(sync_state=1)
    users = await get_users()
    for user in users:
        req = requests.post(f'{HOST}/users', json=user)
        if req.status_code == 200:
            await Users.filter(unique_id=user['unique_id']).update(sync_state=1)
    students = await Students.filter(sync_state=0).all().prefetch_related('state', 'branch', 'governorate', 'institute',
                                                                          'poster')
    for student in students:
        json_student = student_json(student)
        req = requests.post(f'{HOST}/student', json=json_student)
        if req.status_code == 200:
            await Students.filter(unique_id=json_student['unique_id']).update(sync_state=1)
    students = await Students.all().prefetch_related('state', 'branch', 'governorate', 'institute',
                                                     'poster')
    for student_install in students:
        stu_install = await StudentInstallments.filter(student_id=student_install.id, sync_state=0).all(). \
            prefetch_related(
            'installment')
        for insta in stu_install:
            json_install = {"date": str(insta.date), "amount": insta.amount, "unique_id": insta.unique_id,
                            "invoice": insta.invoice,
                            "install_unique_id": insta.installment.unique_id,
                            "student_unique_id": student_install.unique_id}
            req = requests.post(
                f'{HOST}/student_installment', json=json_install)
            if req.status_code == 200:
                await StudentInstallments.filter(id=insta.id).update(sync_state=1)
    all_del = await get_del()
    req = requests.post(f'{HOST}/del', json=all_del)
    students_patch, states_patch, students_installment_patch, users_patch = await get_edits()
    for student_patch in students_patch:
        student_patch = await Students.filter(unique_id=student_patch).first().prefetch_related('state', 'branch',
                                                                                                'governorate',
                                                                                                'institute',
                                                                                                'poster')
        json_stu = student_json(student_patch)
        json_stu['patch'] = True
        req = requests.post(f'{HOST}/student', json=json_stu)
        if req.status_code == 200:
            await TemporaryPatch.filter(unique_id=json_stu['unique_id']).update(sync_state=1)
    for state_patch in states_patch:
        state_patch = await States.filter(unique_id=state_patch).first()
        req = requests.post(f"{HOST}/state", json={"name": state_patch.name,
                                                   "unique_id": state_patch.unique_id,
                                                   "patch": True})
        if req.status_code == 200:
            await TemporaryPatch.filter(unique_id=state_patch.unique_id).update(sync_state=1)

    for student_installment_patch in students_installment_patch:
        install_patch = await StudentInstallments.filter(unique_id=student_installment_patch).first().prefetch_related(
            'student', 'installment')
        if install_patch:
            data_patch = {"date": str(install_patch.date), "amount": install_patch.amount,
                          "unique_id": install_patch.unique_id,
                          "invoice": install_patch.invoice,
                          "install_unique_id": install_patch.installment.unique_id,
                          "student_unique_id": install_patch.student.unique_id, "patch": True}
            req = requests.post(f'{HOST}/student_installment', json=data_patch)
            if req.status_code == 200:
                await TemporaryPatch.filter(unique_id=install_patch.unique_id).update(sync_state=1)
    for user_auth in users_patch:
        user = await Users.filter(unique_id=user_auth).first()
        auths = await UserAuth.filter(user_id=user.id).all().prefetch_related('state')
        authority = []
        for auth in auths:
            st = await States.filter(id=auth.state.id).first()
            authority.append({"state_unique_id": st.unique_id,
                              "unique_id": auth.unique_id})
        user_json = {
            "username": user.username, "password": user.password, "authority": authority, "unique_id": user.unique_id
        }
        req = requests.post(f'{HOST}/users', json=user_json)
        if req.status_code == 200:
            await TemporaryPatch.filter(unique_id=user.unique_id).update(sync_state=1)
    await get_all()
    return {
        "success": True
    }
