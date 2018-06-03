from flask import Flask, request
from pymongo import MongoClient
import smtplib
import config #file that is stored wherever it's comfortable. In this case in the same folder.

client = MongoClient()
app = Flask(__name__)
availableSymbols = [chr(i) for i in range(48,58)] + [chr(i) for i in range(65,91)] + [chr(i) for i in range(97,123)] #a-z + A-Z + 0-9
smtpPort = 587
smtpHost = "smtp.gmail.com"

def confirmLink():
    pass

def validation(data):
    if len(data)<6:
        return "Too short. Should be longer than 6 symbols"
    if len(data)>25:
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
    dictUser = {"email": thisEmail, "login": thisLogin, "password": thisPass}

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
            smtpObj.sendmail(config.email, thisEmail, config.confirmText + confirmLink())
        except:
            return "Bad email."
        else:
            usersCol.insert_one(dictUser)
            return "Check your email."

    else:
        return resultOfValidation[0]+'\n'+resultOfValidation[1]

@app.route('/confirmation', methods = ['POST'])
def confirmation():
    pass


if __name__ == '__main__':
    app.run(debug=False, port=3000)