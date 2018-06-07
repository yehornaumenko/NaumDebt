from flask import Flask, request
from pymongo import MongoClient
import smtplib
import secrets
import string
import config #file that is stored wherever it's comfortable. In this case in the same folder.

client = MongoClient()
app = Flask(__name__)
availableSymbols = list(string.ascii_letters + string.digits) #a-z + A-Z + 0-9
smtpPort = 587
smtpHost = "smtp.gmail.com"
IP = "\nhttp://178.150.137.228:5303" #we can change port

def confirmLink(token):
    return IP+"/confirmation?token="+str(token)

def validation(data):
    if len(data) < 6:
        return "Too short. Should be longer than 6 symbols"
    if len(data) > 25:
        return "Too long. Should be shorter than 25 symbols"
    for i in range(len(data)):
        if i not in availableSymbols:
            return "Bad symbols. You can use just: a-z, A-Z, 0-9."
    return True

@app.route('/register', methods = ['GET'])
def register():
    db = client.debts
    usersCol = db.users
    thisEmail = request.values["email"]
    thisLogin = request.values["login"]
    thisPass = request.values["password"]
    token = secrets.token_hex(16)
    dictUser = {"email": thisEmail, "login": thisLogin, "password": thisPass, "token": token, "status": "inactive"}

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
            print(config.confirmText + confirmLink(token))
            smtpObj.sendmail(config.email, thisEmail, config.confirmText + confirmLink(token))
        except:
            print("EMAIL EXCEPTION")
            return "Bad email."
        else:
            usersCol.insert_one(dictUser)
            return "Check your email."

    else:
        return resultOfValidation[0]+'\n'+resultOfValidation[1]

@app.route('/confirmation', methods = ['GET'])
def confirmation():
    db = client.debts
    usersCol = db.users
    thisToken = request.values["token"]

    currentUser = usersCol.find_one({"token": thisToken})

    if currentUser:
        usersCol.update_one({"_id": currentUser["_id"]}, {"$set": {"status": "active"}})
        return "You've activated your account."
    else:
        return "Wrond token. May be you changed link in email."


if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=False, port=5303)
