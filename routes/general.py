from fastapi import APIRouter
from models.models import Institutes, Governorates, States, Students, Installments, StudentInstallments
from tortoise.transactions import in_transaction
from schemas.general import GeneralSchema, Student, StudentInstall

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
    for q in query:
        q.update({"success": True, "total_states": await States.all().count()})
    return query


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
        new = States(name=schema.name)
        await new.save(using_db=conn)
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
#     "first_phone_number": "1",
#     "second_phone_number": "1",
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
        new = Students(name=schema.name, school=schema.school, branch_id=schema.branch_id,
                       governorate_id=schema.governorate_id, institute_id=schema.institute_id,
                       state_id=schema.state_id, first_phone=schema.first_phone_number,
                       second_phone=schema.second_phone_number, code=schema.code, telegram_user=schema.telegram_username
                       , created_at=schema.created_at, note=schema.note, total_amount=schema.total_amount,
                       remaining_amount=schema.remaining_amount, poster_id=schema.poster_id)
        await new.save(using_db=conn)
        for student_install in schema.installments:
            new_student_install = StudentInstallments(installment_id=student_install.install_id,
                                                      date=student_install.date,
                                                      amount=student_install.amount, invoice=student_install.invoice,
                                                      student_id=new.id)
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
#     "first_phone_number": "1",
#     "second_phone_number": "1",
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
    await Students.filter(id=student_id).update(name=schema.name, school=schema.school, branch_id=schema.branch_id,
                                                governorate_id=schema.governorate_id, institute_id=schema.institute_id,
                                                state_id=schema.state_id, first_phone=schema.first_phone_number,
                                                second_phone=schema.second_phone_number, code=schema.code,
                                                telegram_user=schema.telegram_username
                                                , created_at=schema.created_at, note=schema.note,
                                                total_amount=schema.total_amount,
                                                remaining_amount=schema.remaining_amount, poster_id=schema.poster_id)
    for student_install in schema.installments:
        await StudentInstallments.filter(student_id=student_id).update(installment_id=student_install.install_id,
                                                                       date=student_install.date,
                                                                       amount=student_install.amount,
                                                                       invoice=student_install.invoice)
    name = await Students.filter(id=student_id).first().values('name')
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
    student = await Students.filter(id=student_id).first().values('name')
    name = student['name']
    await Students.filter(id=student_id).delete()
    return {
        "success": True,
        "name": name
    }


# GET '/students'
# = get students bulky
# Response:
# [
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
# ]
@general_router.get('/students')
async def get_students():
    students = await Students.all().prefetch_related('branch', 'governorate', 'institute', 'state', 'poster').all()
    students_list = []
    student_json = {}
    for stu in students:
        student_json['name'] = stu.name
        student_json['id'] = stu.id
        student_json['school'] = stu.school
        student_json['code'] = stu.code
        student_json['first_phone'] = stu.first_phone
        student_json['second_phone'] = stu.second_phone
        student_json['telegram_user'] = stu.telegram_user
        student_json['created_at'] = stu.created_at
        student_json['note'] = stu.note
        student_json['total_amount'] = stu.total_amount
        student_json['remaining_amount'] = stu.remaining_amount
        if stu.branch is not None:
                student_json['branch'] = {"id": stu.branch.id, 'name': stu.branch.name}
        if stu.governorate is not None:
            student_json['governorate'] = {"id": stu.governorate.id, "name": stu.governorate.name}
        if stu.institute is not None:
            student_json['institute'] = {'id': stu.institute.id, "name": stu.institute.name}
        if stu.state is not None:
            student_json['state'] = {'id': stu.state.id, 'name': stu.state.name}
        if stu.poster is not None:
            student_json['poster'] = {'id': stu.poster.id, 'name': stu.poster.name}
        student_install = await StudentInstallments.filter(student_id=stu.id).prefetch_related('installment').all()
        install_list = []
        for stu_install in student_install:
            single_install = {"id": stu_install.id, "date": stu_install.date, "amount": stu_install.amount,
                              "invoice": stu_install.invoice, "installment_id": stu_install.installment.id,
                              "installment_name": stu_install.installment.name}
            install_list.append(single_install)
        student_json['installments'] = install_list
        students_list.append(student_json)
        student_json = {}

    return students_list