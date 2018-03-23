from flask import Flask, jsonify, request
from pymodm import connect
import models
import datetime

app = Flask(__name__)
connect("mongodb://localhost:27017/bme590")


@app.route("/api/heart_rate/<user_email>", methods=["GET"])
def return_hrs(user_email):
    """
    Returns all measured heart rates for a user

    :param: String user_email: user's email used to identify user in database
    :return: all the measured heart rates
    :rtype: list of strings
    """
    try:
        user = models.User.objects.raw({"_id": user_email}).first()
        heart_rates = user.heart_rate

    except FileNotFoundError:
        return jsonify({"message": "User does not exist"}), 404

    data = {
        "hrs": heart_rates,
    }
    return jsonify(data)


@app.route("/api/heart_rate/average/<user_email>", methods=["GET"])
def return_avg_hr(user_email):
    """
    Returns average of all measured heart rates for a user

    :param: String user_email: user's email used to identify user in database
    :return: average of all heart rates
    :rtype: float
    """
    try:
        user = models.User.objects.raw({"_id": user_email}).first()
        sum = 0
        for x in user.heart_rate:
            sum = sum + x
        avg = sum / len(user.heart_rate)

    except FileNotFoundError:
        return jsonify({"message": "User does not exist"}), 404

    data = {
        "avg_hr": avg
    }
    return jsonify(data)


@app.route("/api/heart_rate", methods=["POST"])
def add_hr():
    """
        Appends heart rate and measurement time to a user in database,
        or adds new user to database if user does not already exist

        """
    r = request.get_json()
    try:
        user_email = r["user_email"]
        user_age = r["user_age"]
        heart_rate = r["heart_rate"]
    except ValueError:
        return jsonify({"message": "data missing user_email, "
                                   "user_age or heart rate field(s)"}), 400

    exists = False
    for user in models.User.objects.raw({}):
        if user.email == r["user_email"]:
                exists = True

    if exists is True:
        user = models.User.objects.raw({"_id": r["user_email"]}).first()
        user.heart_rate.append(r["heart_rate"])
        user.heart_rate_times.append((datetime.datetime.now()))
        user.save()
    else:
        u = models.User(email=r["user_email"], age=r["user_age"],
                        heart_rate=[r["heart_rate"]],
                        heart_rate_times=[(datetime.datetime.now())])
        u.save()


@app.route("/api/heart_rate/interval_average", methods=["POST"])
def calc_interval_avg():
    """
        Returns average of all measured heart rates that occur
        after a certain time and whether this average is
        tachycardic or not

        :return: average of all heart rates since a specified time,
        average_heart_rate_since and if average heart rate
        is tachycardic, is_tachycardic
        :rtype: json file
        """

    r = request.get_json()
    try:
        user_email = r["user_email"]
        time = r["heart_rate_average_since"]
    except ValueError:
        return jsonify({"message": "data missing user_email or "
                        "heart_rate_average_since field(s)"}), 400
    try:
        user = models.User.objects.raw({"_id": r["user_email"]}).first()
    except FileNotFoundError:
        return jsonify({"message": "User does not exist"}), 404
    try:
        time = datetime.datetime.strptime(r["heart_rate_average_since"],
                                          "%Y-%m-%d %H:%M:%S.%f")
    except TypeError:
        return jsonify({"message": "format of time is incorrect"}), 400
    for i in range(0, len(user.heart_rate_times)):
        if user.heart_rate_times[i] > time:
            index = i
            break

    sum = 0
    for x in range(index, len(user.heart_rate)):
        sum = sum + user.heart_rate[x]

    avg_since = sum / (len(user.heart_rate) - index)
    is_tach = is_tachycardic(avg_since, user.age)
    data = {
        "average_heart_rate_since": avg_since,
        "is_tachycardic": is_tach
    }
    return jsonify(data)


def is_tachycardic(average, age):
    """
        Returns whether a heart rate in bpm is tachycardic

        :param: float average: heart rate in bpm
        :param: float age: the age of patient
        :return: true if heart rate is tachycardic
        :rtype: boolean
        """
    ages = [0.5, 1, 3, 5, 8, 12, 15]
    bpm = [175, 169, 151, 137, 133, 130, 119]

    try:
        for i in range(0, len(ages)):
            if age < ages[i]:
                if average > bpm[i]:
                    return True
                else:
                    return False

        if age > 15:
            if average > 100:
                return True
        return False

    except TypeError:
        return jsonify({"message": "Average and Age must be numbers"}), 400
