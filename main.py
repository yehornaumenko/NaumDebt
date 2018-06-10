from flask import Flask, request
from pymongo import MongoClient
import smtplib
import secrets
import string
import bcrypt
# file that is stored wherever it's comfortable. In this case in the same
# folder.
import config

client = MongoClient()
app = Flask(__name__)
availableSymbols = list(
    string.ascii_letters +
    string.digits)  # a-z + A-Z + 0-9
smtpPort = 587
smtpHost = "smtp.gmail.com"
IP = "\nhttp://178.150.137.228:5303"  # we can change port

# to validate pass or login
MAX_TEXT_LENGTH = 24
MIN_TEXT_LENGTH = 6


def doLogin(user, collection, password):
    if user:
        if user["status"] == "active":
            if bcrypt.checkpw(password, user["password"]):
                token = secrets.token_hex(16)
                collection.update_one({"_id": user["_id"]}, {
                                      "$set": {"token": token}})
                return token
            else:
                return "Bad password."
        else:
            return "Activate your account. Check email."


def validation(data):
    if len(data) < MIN_TEXT_LENGTH:
        return "Too short. Should be longer than 6 symbols"
    if len(data) > MAX_TEXT_LENGTH:
        return "Too long. Should be shorter than 25 symbols"
    for i in range(len(data)):
        if i not in availableSymbols:
            return "Bad symbols. You can use just: a-z, A-Z, 0-9."
    return True


@app.route('/register', methods=['POST'])
def register():
    db = client.debts
    usersCol = db.users

    thisEmail = request.values.get("email")
    thisLogin = request.values.get("login")
    thisPass = request.values.get("password")

    # We check validity of not hashed pass but store in DB hashed
    hashPass = bcrypt.hashpw(bytes(thisPass, 'utf-8'), bcrypt.gensalt())
    token = secrets.token_hex(16)

    dictUser = {
        "email": thisEmail,
        "login": thisLogin,
        "password": hashPass,
        "token": token,
        "status": "inactive"}
    currentUser = usersCol.find_one({"email": thisEmail})

    if currentUser:
        return "This email has been used."

    currentUser = usersCol.find_one({"login": thisLogin})

    if currentUser:
        return "This login has been used."

    resultOfValidation = [validation(thisPass), validation(thisLogin)]
    if resultOfValidation[0] and resultOfValidation[1]:
        try:
            smtpObj = smtplib.SMTP(smtpHost, smtpPort)
            smtpObj.starttls()
            smtpObj.login(config.email, config.password)
            print(config.confirmText + str(lambda token: IP + \
                  "/confirmation?token=" + str(token)))
            smtpObj.sendmail(config.email, thisEmail, config.confirmText +
                             str(lambda token: IP + "/confirmation?token=" + str(token)))
        except BaseException:
            print("EMAIL EXCEPTION")
            return "Bad email."
        else:
            usersCol.insert_one(dictUser)
            return "Check your email."

    else:
        return resultOfValidation[0] + '\n' + resultOfValidation[1]


@app.route('/confirmation', methods=['GET'])
def confirmation():
    db = client.debts
    usersCol = db.users
    thisToken = request.values["token"]

    currentUser = usersCol.find_one({"token": thisToken})

    if currentUser:
        usersCol.update_one({"_id": currentUser["_id"]}, {
                            "$set": {"status": "active"}})
        usersCol.update_one({"_id": currentUser["_id"]}, {
                            "$unset": {"token": ""}})
        return "You've activated your account."
    else:
        return "Wrong token. May be you changed link in email."


@app.route('/login', methods=['POST'])
def login():
    db = client.debts
    usersCol = db.users
    # User can enter in login line login or email, so let's call it "head"
    thisHead = request.values["head"]
    thisPass = request.values["password"]

    if '@' in thisHead:
        currentUser = usersCol.find_one({"email": thisHead})
        doLogin(currentUser, usersCol, thisPass)
    else:
        currentUser = usersCol.find_one({"login": thisHead})
        doLogin(currentUser, usersCol, thisPass)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5303)
