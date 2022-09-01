import os
import signal
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends
from models.models import Institutes, Governorates, States, Students, Installments, StudentInstallments, \
    Users, UserAuth, TemporaryPatch, TemporaryDelete, Branches, Posters
from tortoise.transactions import in_transaction
from schemas.general import GeneralSchema, Student, StudentInstall, User, Login
import hashlib
import datetime
from fastapi_pagination import paginate, Params as ps

# todo: complete sync_state
# todo: complete api sync with online interaction
general_router = APIRouter()


# GET `/states`
#
# - Get all states from the database.
# - Request Arguments: None
# - Returns: list of states.
#
# Example Response `{
#     "states": [
#         {
#             "id": 1,
#             "name": "منصور صيفي",
#         }
#     ],
#     "total_states": 11,
#     "success": true,
# }`
@general_router.get('/states')
async def get_states():
    query = await States.all().values('id', 'name')

    return {"success": True, "total_states": await States.all().count(), "states": query}


# POST `/states`
#
# - Add a state to the database.
# - Request Body: Name.
# - Returns: name of state.
#
# Example Request Payload `{
#     "name": "1"
# }`
@general_router.post('/states')
async def post_state(schema: GeneralSchema):
    async with in_transaction() as conn:
        unique_id = str(uuid4())
        new = States(name=schema.name, unique_id=unique_id)
        await new.save(using_db=conn)
        users = await Users.filter(super=1).all()
        for user in users:
            sup = UserAuth(state_id=new.id, user_id=user.id,
                           unique_id=str(uuid4()))
            await sup.save(using_db=conn)
            await Users.filter(super=1).update(sync_state=0)

        for user_id in schema.users:
            auth = UserAuth(state_id=new.id, user_id=user_id.id,
                            unique_id=str(uuid4()))
            await auth.save(using_db=conn)
            await Users.filter(id=user_id.id).update(sync_state=0)

    return {
        "success": True,
        "name": new.name
    }


# PATCH `/states/{state_id}`
#
# - Edit a state to the database.
# - Request Body: Name.
# - Returns: name of state.
#
# Example Request Payload `{
#     "name": "1"
# }`
#
# Example Response `{
#     "name": "1"
#     "success": true
# }`
@general_router.patch('/states/{state_id}')
async def patch_state(state_id, schema: GeneralSchema):
    await States.filter(id=state_id).update(name=schema.name)
    patch = await States.filter(id=state_id).first().values('unique_id')
    temporary = await TemporaryPatch.filter(unique_id=patch['unique_id']).first()
    async with in_transaction() as conn:
        if temporary is None:
            new = TemporaryPatch(unique_id=patch['unique_id'], model_id=2)
            await new.save(using_db=conn)
        for user in await Users.filter(super=0):
            await UserAuth.filter(state_id=state_id, user_id=user.id).delete()
        for user_id in schema.users:
            auth = UserAuth(state_id=state_id,
                            user_id=user_id.id, unique_id=str(uuid4()))
            await auth.save(using_db=conn)
            await Users.filter(id=user_id.id).update(sync_state=0)

    return {
        "success": True,
        "name": schema.name
    }


# DELETE `/states/<state_id>`
#
# - Delete a state from the database.
# - Request Arguments: None.
# - Returns: name of state.
#
# Example Response `{
#     "name": "ينمبلا",
#     "success": true
# }`
@general_router.delete('/states/{state_id}')
async def del_state(state_id):
    q = await States.filter(id=state_id).first()
    await States.filter(id=state_id).delete()
    await TemporaryPatch.filter(unique_id=q.unique_id).delete()
    async with in_transaction() as conn:
        new = TemporaryDelete(unique_id=q.unique_id, model_id=2)
        await new.save(using_db=conn)
    return {
        "success": True,
        "name": q.name
    }


# POST `/students`
# - Add a student to the database.
# - Request Arguments: None.
# - Returns: name of student.
# Example Request Payload `{
#     "name": "1",
#     "school": "1",
#     "state_id": int
#     "branch_id": "1",
#     "institute_id": "1",
#     "governorate_id": "1",
#     "first_phone": "1",
#     "second_phone": "1",
#     "poster_id": "1",
#     "code": "1",
#     "telegram_username": "1",
#     "total_amount": "1",
#     "installments":[{"install_id":int, "amount":float, "invoice":int, "date":str}, {}, {},{}]
#     "remaining_amount": "1",
#     "note": "1",
#     "created_at":str
# }`
# Example Response `{
#     "name": "جبار علي",
#     "success": true
# }`
@general_router.post('/students')
async def post_student(schema: Student):
    async with in_transaction() as conn:
        unique_id = str(uuid4())
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        poster_id = None
        if schema.poster_id != 0:
            poster_id = schema.poster_id
        new = Students(name=schema.name, school=schema.school, branch_id=schema.branch_id,
                       governorate_id=schema.governorate_id, institute_id=schema.institute_id,
                       state_id=schema.state_id, first_phone=schema.first_phone,
                       second_phone=schema.second_phone, code_1=schema.code_1, code_2=schema.code_2,
                       telegram_user=schema.telegram_username, created_at=date_now, note=schema.note, total_amount=schema.total_amount,
                       remaining_amount=schema.remaining_amount, poster_id=poster_id, unique_id=unique_id)
        await new.save(using_db=conn)
        for student_install in schema.installments:
            unique_id2 = str(uuid4())
            new_student_install = StudentInstallments(installment_id=student_install.install_id,
                                                      date=student_install.date,
                                                      amount=student_install.amount, invoice=student_install.invoice,
                                                      student_id=new.id, unique_id=unique_id2)
            await new_student_install.save(using_db=conn)
        return {"success": True,
                "name": new.name}


# Patch `/students/{student_id}`
# - edit the student .
# - Request Arguments: None.
# - Returns: name of student.
# Example Request Payload `{
#     "name": "1",
#     "school": "1",
#     "state_id": int
#     "branch_id": "1",
#     "institute_id": "1",
#     "governorate_id": "1",
#     "first_phone": "1",
#     "second_phone": "1",
#     "poster_id": "1",
#     "code": "1",
#     "telegram_username": "1",
#     "total_amount": "1",
#     "installments":[{"install_id":int, "amount":float, "invoice":int, "date":str}, {}, {},{}]
#     "remaining_amount": "1",
#     "note": "1",
#     "created_at":str
# }`
# Example Response `{
#     "name": "جبار علي",
#     "success": true
# }`

@general_router.patch('/students/{student_id}')
async def patch_student(student_id, schema: Student):
    date_now = datetime.datetime.now().strftime('%Y-%m-%d')
    poster_id = None
    if schema.poster_id != 0:
        poster_id = schema.poster_id
    await Students.filter(id=student_id).update(name=schema.name, school=schema.school,
                                                branch_id=schema.branch_id,
                                                governorate_id=schema.governorate_id,
                                                institute_id=schema.institute_id,
                                                state_id=schema.state_id,
                                                first_phone=schema.first_phone,
                                                second_phone=schema.second_phone,
                                                code_1=schema.code_1,
                                                code_2=schema.code_2,
                                                telegram_user=schema.telegram_username, created_at=date_now,
                                                note=schema.note,
                                                total_amount=schema.total_amount,
                                                remaining_amount=schema.remaining_amount,
                                                poster_id=poster_id)
    name = await Students.filter(id=student_id).first().values('name', 'unique_id')
    async with in_transaction() as conn:
        new = TemporaryPatch(unique_id=name['unique_id'], model_id=1)
        await new.save(using_db=conn)
    for student_install in schema.installments:
        await StudentInstallments.filter(student_id=student_id, installment_id=student_install.install_id).update(
            date=student_install.date,
            amount=student_install.amount,
            invoice=student_install.invoice)
        q = await StudentInstallments.filter(student_id=student_id, installment_id=student_install.install_id
                                             ).first().values('unique_id')
        async with in_transaction() as coon:
            new = TemporaryPatch(unique_id=q['unique_id'], model_id=3)
            await new.save(using_db=coon)

    name = name['name']
    return {
        "success": True,
        "name": name
    }


# DELETE `/students/<student_id>`
#
# - Delete a student from the database.
# - Request Arguments: None.
# - Returns: name of students.
#
# Example Response `{
#     "name": "جبار علي",
#     "success": true
# }`
@general_router.delete('/students/{student_id}')
async def del_student(student_id):
    student = await Students.filter(id=student_id).first().values('name', 'unique_id')
    name = student['name']
    installments = await StudentInstallments.filter(student_id=student_id).all()
    for installment in installments:
        await TemporaryPatch.filter(unique_id=installment.unique_id).delete()

    await Students.filter(id=student_id).delete()

    await TemporaryPatch.filter(unique_id=student['unique_id']).delete()

    async with in_transaction() as conn:
        new = TemporaryDelete(unique_id=student['unique_id'], model_id=1)
        await new.save(using_db=conn)
    return {
        "success": True,
        "name": name
    }


# GET '/students'
# = get students bulky
# Response:
# "students":[
#   {
#     "name": "حسين فاضل",
#     "id": 1,
#     "school": "المستقبل",
#     "code": 7879,
#     "first_phone": 886786,
#     "second_phone": 56789,
#     "telegram_user": "string",
#     "created_at": null,
#     "note": "string",
#     "total_amount": 1000,
#     "remaining_amount": 0,
#     "branch": {
#       "id": 1,
#       "name": "احيائي"
#     },
#     "governorate": {
#       "id": 1,
#       "name": "بغداد"
#     },
#     "institute": {
#       "id": 1,
#       "name": "البنوك"
#     },
#     "state": {
#       "id": 1,
#       "name": "بغداد عربي انكليزي"
#     },
#     "poster": {
#       "id": 1,
#       "name": "اخضر"
#     },
#     "installments": [
#       {
#         "id": 1,
#         "date": null,
#         "amount": 0,
#         "invoice": 0,
#         "installment_id": 1,
#         "installment_name": "القسط الاول"
#       },
#       {
#         "id": 2,
#         "date": null,
#         "amount": 0,
#         "invoice": 0,
#         "installment_id": 2,
#         "installment_name": "القسط الثاني"
#       }
#     ]
#   }
# ],
# "success":True}
class Params(ps):
    search: Optional[str] = None
    page: Optional[int] = 1
    number_of_students: int = 100


@general_router.get('/students')
async def get_students():
    students = await Students.all().prefetch_related('branch', 'governorate', 'institute', 'state', 'poster').all()
    students_list = []
    student_json = {}
    for stu in students:
        student_json['name'] = stu.name
        student_json['id'] = stu.id
        student_json['school'] = stu.school
        student_json['code_1'] = stu.code_1
        student_json['code_2'] = stu.code_2
        student_json['first_phone'] = stu.first_phone
        student_json['second_phone'] = stu.second_phone
        student_json['telegram_username'] = stu.telegram_user
        student_json['created_at'] = stu.created_at
        student_json['note'] = stu.note
        student_json['total_amount'] = stu.total_amount
        student_json['remaining_amount'] = stu.remaining_amount
        if stu.branch is not None:
            student_json['branch'] = {
                "id": stu.branch.id, 'name': stu.branch.name}
        if stu.governorate is not None:
            student_json['governorate'] = {
                "id": stu.governorate.id, "name": stu.governorate.name}
        if stu.institute is not None:
            student_json['institute'] = {
                'id': stu.institute.id, "name": stu.institute.name}
        if stu.state is not None:
            student_json['state'] = {
                'id': stu.state.id, 'name': stu.state.name}
        if stu.poster is not None:
            student_json['poster'] = {
                'id': stu.poster.id, 'name': stu.poster.name}
        student_install = await StudentInstallments.filter(student_id=stu.id).prefetch_related('installment').all()
        install_list = []
        for stu_install in student_install:
            single_install = {"install_id": stu_install.installment.id, "date": stu_install.date, "amount": stu_install.amount,
                              "invoice": stu_install.invoice, "installment_id": stu_install.installment.id,
                              "installment_name": stu_install.installment.name}
            install_list.append(single_install)
        student_json['installments'] = install_list
        students_list.append(student_json)
        student_json = {}

    return {"students": students_list, "success": True}


@general_router.get('/students-names')
async def get_students_names():
    students = await Students.all().values("id", "name")

    return {"students": students, "success": True}


@general_router.get('/states/{state_id}/students')
async def get_state_students(state_id, params: Params = Depends()):

    if params.search is not None:
        count = await Students.filter(state_id=state_id, name__icontains=params.search).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                                                         'poster').all()
        students = await Students.filter(state_id=state_id, name__icontains=params.search).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                                                            'poster').all().limit(params.number_of_students).offset((params.page - 1) *
                                                                                                                                                                    params.number_of_students)
    else:
        count = await Students.filter(state_id=state_id).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                          'poster').all()
        students = await Students.filter(state_id=state_id).prefetch_related('branch', 'governorate', 'institute', 'state',
                                                                             'poster').all().limit(params.number_of_students).offset((params.page - 1) *
                                                                                                                                     params.number_of_students)
    count = len(count)
    students_list = []
    student_json = {}
    for stu in students:
        student_json['name'] = stu.name
        student_json['id'] = stu.id
        student_json['school'] = stu.school
        student_json['code_1'] = stu.code_1
        student_json['code_2'] = stu.code_2
        student_json['first_phone'] = stu.first_phone
        student_json['second_phone'] = stu.second_phone
        student_json['telegram_username'] = stu.telegram_user
        student_json['created_at'] = stu.created_at
        student_json['note'] = stu.note
        student_json['total_amount'] = stu.total_amount
        student_json['remaining_amount'] = stu.remaining_amount
        if stu.branch is not None:
            student_json['branch'] = {
                "id": stu.branch.id, 'name': stu.branch.name}
        if stu.governorate is not None:
            student_json['governorate'] = {
                "id": stu.governorate.id, "name": stu.governorate.name}
        if stu.institute is not None:
            student_json['institute'] = {
                'id': stu.institute.id, "name": stu.institute.name}
        if stu.state is not None:
            student_json['state'] = {
                'id': stu.state.id, 'name': stu.state.name}
        if stu.poster is not None:
            student_json['poster'] = {
                'id': stu.poster.id, 'name': stu.poster.name}
        student_install = await StudentInstallments.filter(student_id=stu.id).prefetch_related('installment').all()
        install_list = []
        for stu_install in student_install:
            single_install = {"date": stu_install.date, "amount": stu_install.amount,
                              "invoice": stu_install.invoice, "install_id": stu_install.installment.id,
                              "installment_name": stu_install.installment.name}
            install_list.append(single_install)
        student_json['installments'] = install_list
        students_list.append(student_json)
        student_json = {}
    if len(students) <= params.number_of_students:
        pages = 1
    else:
        pages = int(round(len(students) / params.number_of_students))

    return {"students": students_list, "success": True,
            "total_students": count,
            "page": params.page,
            "total_pages": pages}


# GET `/users`
#
# - Get users from database.
# - Request Arguments: None
# - Returns: list of students.
#
# Example Response `{
#   "users": [
#     {
#       "id": 1,
#       "username": "krvhrv",
#       "authority": [
#         {
#           "authority_id": 1,
#           "state": "الكويت",
#           "state_id": 1
#         }
#       ]
#     }
#   ],
#   "total_users": 1,
#   "success": true
# }'
@general_router.get('/users')
async def get_users():
    users = await Users.all()
    result_list = []
    for user in users:
        result_json = {"id": user.id, "username": user.username,
                       'name': user.name, "super": user.super}
        authority = []
        auth = await UserAuth.filter(user_id=user.id).prefetch_related('state').all()
        for au in auth:
            auth_json = {"authority_id": au.id,
                         "name": au.state.name, "id": au.state.id}
            authority.append(auth_json)
        result_json['authority'] = authority
        result_list.append(result_json)
    return {
        "users": result_list,
        "total_users": await Users.all().count(),
        "success": True
    }


# POST `/users`
# - Add user in database.
# - Request Arguments: None
# - Returns: None.
# Example Request Payload `{
#     "username": "1",
#     "password": "22",
#     "authority": [
#         {
#             "state_id": 1,
#             "state": "نرس"
#         }
#     ],
# }`
# Example Response `{
#     "success": true
# }`
@general_router.post('/users')
async def post_user(schema: User):
    async with in_transaction() as conn:
        unique_id = str(uuid4())
        password = hashlib.md5(schema.password.encode())
        new = Users(username=schema.username, password=password.hexdigest(
        ), unique_id=unique_id, name=schema.name)
        if schema.super:
            new = Users(username=schema.username, password=password.hexdigest(), unique_id=unique_id, name=schema.name,
                        super=1)
        await new.save(using_db=conn)
        if not schema.super:
            for state in schema.authority:
                unique_id = str(uuid4())
                auth = UserAuth(
                    user_id=new.id, state_id=state.id, unique_id=unique_id)
                await auth.save(using_db=conn)
        else:
            for state in await States.all():
                unique_id = str(uuid4())
                auth = UserAuth(
                    user_id=new.id, state_id=state.id, unique_id=unique_id)
                await auth.save(using_db=conn)
    return {
        "success": True
    }


# PATCH `/users/{user_id}`
# - Add user in database.
# - Request Arguments: None
# - Returns: None.
# Example Request Payload `{
#     "username": "1",
#     "password": "22",
#     "authority": [
#         {
#             "state_id": 1,
#             "state": "نرس"
#         }
#     ],
# }`
# Example Response `{
#     "success": true
# }`
@general_router.patch('/users/{user_id}')
async def patch_user(user_id, schema: User):
    get_user = await Users.filter(id=user_id).first()
    password = hashlib.md5(schema.password.encode())
    await Users.filter(id=user_id).update(username=schema.username, password=password.hexdigest(), name=schema.name,
                                          sync_state=0, super=0)
    if schema.super:
        await Users.filter(id=user_id).update(username=schema.username, password=password.hexdigest(), name=schema.name,
                                              sync_state=0, super=1)
    # get_auth = await UserAuth.filter(user_id=get_user.id).first()
    await UserAuth.filter(user_id=get_user.id).delete()
    async with in_transaction() as conn:
        for state in schema.authority:
            unique_id = str(uuid4())
            auth = UserAuth(user_id=get_user.id,
                            state_id=state.id, unique_id=unique_id)
            await auth.save(using_db=conn)
    return {
        "success": True
    }


# POST - '/login'
# request body:
# {"username": krvhrv, "password": "1234"}
# response: {"success": True}
@general_router.post('/login')
async def login(schema: Login):
    users = await Users.all()
    for user in users:
        if user.username == schema.username:
            password = schema.password.encode()
            password = hashlib.md5(password)
            if user.password == password.hexdigest():
                states = []
                auth = await UserAuth.filter(user_id=user.id).all().prefetch_related('state')
                for state in auth:
                    state = {"name": state.state.name, "id": state.state.id}
                    states.append(state)
                return {
                    "success": True,
                    "token": str(uuid4()),
                    "username": user.username,
                    "name": user.name,
                    "password": user.password,
                    "authority": states,
                    "super": user.super
                }
            else:
                return {
                    "success": False
                }


@general_router.get('/shutdown')
async def shutdown():
    pid = os.getpid()
    os.kill(pid, signal.CTRL_C_EVENT)


@general_router.get('/governorates')
async def get_governorates():
    return {
        "success": True,
        "governorates": await Governorates.all()
    }


@general_router.get('/branches')
async def get_branches():
    return {
        "branches": await Branches.all(),
        "success": True
    }


@general_router.get('/posters')
async def get_posters():
    return {
        "posters": await Posters.all(),
        "success": True
    }


@general_router.get('/institutes')
async def get_institutes():
    return {
        "institutes": await Institutes.all()
    }


@general_router.delete('/users/{user_id}')
async def del_user(user_id):
    get_user = await Users.filter(id=user_id).first()
    await Users.filter(id=user_id).delete()
    async with in_transaction() as conn:
        new = TemporaryDelete(unique_id=get_user.unique_id, model_id=4)
        await new.save(using_db=conn)
    return {
        "success": True, "user": get_user.name
    }


# @general_router.patch('/ss')
# async def sss():
#     await Students.all().update(sync_state=1)
#     await StudentInstallments.all().update(sync_state=1)
#     await States.all().update(sync_state=1)
#     return {
#         "success": True
#     }
