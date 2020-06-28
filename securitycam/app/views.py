import base64
from django.db.models import Avg

import numpy as np
from firebase import firebase
from keras import preprocessing
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.layers.core import Dropout, Flatten, Dense
from keras.models import Sequential
from keras.models import model_from_json
from keras.optimizers import Adam
from django.core.files.base import ContentFile
from .models import *
from .serializer import *
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

firebase = firebase.FirebaseApplication('https://gezginim-uygulamam.firebaseio.com/', None)


# for modeling data
width = 96
height = 96
conv_1 = 16
conv_1_drop = 0.2
conv_2 = 32
conv_2_drop = 0.2
dense_1_n = 1024
dense_1_drop = 0.2
dense_2_n = 512
dense_2_drop = 0.2
lr = 0.001

epochs = 30
batch_size = 32
color_channels = 3

class_names = ["safe", "suspicious"]

def build_model(conv_1_drop=conv_1_drop, conv_2_drop=conv_2_drop,
                dense_1_n=dense_1_n, dense_1_drop=dense_1_drop,
                dense_2_n=dense_2_n, dense_2_drop=dense_2_drop,
                lr=lr):
    model = Sequential()
    model.add(Convolution2D(conv_1, (3, 3),
                            input_shape=(width, height, color_channels),
                            activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(conv_1_drop))

    model.add(Convolution2D(conv_2, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(conv_2_drop))

    model.add(Flatten())

    model.add(Dense(dense_1_n, activation='relu'))
    model.add(Dropout(dense_1_drop))

    model.add(Dense(dense_2_n, activation='relu'))
    model.add(Dropout(dense_2_drop))

    model.add(Dense(len(class_names), activation='softmax'))

    model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=lr))

    return model


def get_model():
    json_file = open('model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load woeights into new model
    loaded_model.load_weights("model.h5")
    print("Loaded Model from disk")

    # compile and evaluate loaded model
    loaded_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=["accuracy"])
    # loss,accuracy = model.evaluate(X_test,y_test)
    # print('loss:', loss)
    # print('accuracy:', accuracy)
    return loaded_model


class SCAddDataAPI(APIView):
    class_names = ["safe", "suspicious"]
    width = 96
    height = 96

    def post(self, request, format=None):
        image_data = self.request.POST.get("image")
        code = self.request.POST.get("code")
        regular = self.request.POST.get("regular")
        image = ContentFile(base64.b64decode(image_data), name='safe.jpg')  # You can save this as file instance.

        systems = SCSystem.objects.filter(code=code)
        result = "No system"
        if systems.count():
            system = systems.first()

            data = SCData()
            data.text = "Unknown"
            data.image = image
            data.system = system
            data.save()

            model = get_model()
            miy = preprocessing.image.load_img("." + data.image.url, target_size=(self.width, self.height))

            miyx = np.expand_dims(miy, axis=0)
            predictions = model.predict(miyx)

            safety = int(predictions[0][0]*100)
            suspicious = int(predictions[0][1]*100)

            firebase.put("/", "safety", str(safety))
            if regular == "no":
                firebase.put("/", "bell", "on")
                firebase.put("/", "data_image", data.image.url)
                data.is_regular = False
            else:
                data.is_regular = True

            if safety < system.security_percent:
                firebase.put("/", "security", "off")
            data.safety = safety
            data.suspicious = suspicious
            data.save()

            result = str(predictions)

        return Response(result)
        # return Response(self.class_names[np.argmax(predictions)])


class SCRegisterAPI(APIView):
    context = {}

    def post(self, request):
        email = self.request.POST.get("email")
        password = self.request.POST.get("password")

        users = User.objects.filter(email=email)
        if users.count() > 0:
            self.context["status"] = "failure"
            self.context["message"] = "email exists!"
        else:
            user = User()
            user.username = email
            user.email = email
            user.set_password(password)
            user.save()
            self.context["status"] = "success"
            self.context["message"] = "successfully registered."
        return Response(self.context)


class SCProfileApi(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        context = {}
        context["user"] = UserSerializer(request.user, many=False).data

        systems = []
        for member in SCMember.objects.filter(user=request.user):
            system = {"membership": member.type, "code": member.system.code, "name": member.system.name, "id": member.system.id, "is_selected": member.is_selected}
            systems.append(system)
        context["systems"] = systems

        return Response(context)


class SCMembersApi(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        context = {}

        members = SCMember.objects.filter(user=request.user, is_selected=True)
        if members.count() > 0:
            mymembers = []
            knownpeople = []
            system = members.first().system
            for member in SCMember.objects.filter(system=system):
                userdata = {"name": member.user.email, "membership": member.type}
                mymembers.append(userdata)

            for person in SCKnownPerson.objects.filter(data__system=system):
                known = {"user_email": person.user.email, "data": SCDataSerializer(person.data, many=False).data}
                knownpeople.append(known)

            context["members"] = mymembers
            context["knownpeople"] = knownpeople
        else:
            context["status"] = "faiure"

        return Response(context)


class SCAddMemberAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    context = {}

    def post(self, request):
        email = self.request.POST.get("email")

        members = SCMember.objects.filter(system__admin=request.user, is_selected=True)

        if members.count() > 0:
            member = members.first()
            users = User.objects.filter(email=email)
            if users.count() > 0:
                user = users.first()
                member_new = SCMember()
                member_new.system = member.system
                member_new.user = user
                member_new.type = 0
                member_new.save()
                self.context["status"] = "success"
                self.context["message"] = "successfully added member to camera system."
            else:
                self.context["status"] = "failure"
                self.context["message"] = "User with this email is not exists!"
        else:
            self.context["status"] = "failure"
            self.context["message"] = "You are not allowed to do this action!"
        return Response(self.context)


class SCCreteSystemAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    context = {}

    def post(self, request):
        code = self.request.POST.get("code")
        name = self.request.POST.get("name")

        members = SCMember.objects.filter(user=request.user, is_selected=True)
        members.update(is_selected=False)

        system = SCSystem()
        system.code = code
        system.name = name
        system.admin = request.user
        system.save()

        member_new = SCMember()
        member_new.user = request.user
        member_new.system = system
        member_new.type = 1
        member_new.is_selected = True
        member_new.save()

        self.context["status"] = "success"
        self.context["message"] = "You have created camera system and selected."

        return Response(self.context)


class SCSelectSystemAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    context = {}

    def post(self, request):
        code = self.request.POST.get("code")

        SCMember.objects.filter(user=request.user, is_selected=True).update(is_selected=False)

        SCMember.objects.filter(system__code=code).update(is_selected=True)

        self.context["status"] = "success"
        self.context["message"] = "You have selected camera system successfully."

        return Response(self.context)


class SCSecureStatusDataAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    context = {}

    def post(self, request):
        data_id = self.request.POST.get("data_id")
        person_name = self.request.POST.get("person_name")
        is_secure = self.request.POST.get("is_secure")

        data = SCData.objects.get(id=data_id)

        if is_secure == "yes":
            data.safety = 100
            data.suspicious = 0
            if person_name != "":
                data.text = person_name
                data.save()
                persons = SCKnownPerson.objects.filter(user=self.request.user, data=data)
                if persons.count() > 0:
                    person = persons.first()
                else:
                    person = SCKnownPerson()
                person.user = self.request.user
                person.data = data
                person.name = person_name
                person.save()
        else:
            data.safety = 0
            data.suspicious = 100
            data.save()

        self.context["status"] = "success"
        self.context["message"] = "Process successfully completed."

        return Response(self.context)


class SCDatasApi(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        context = {}

        members = SCMember.objects.filter(user=request.user, is_selected=True)
        context["selected_membership_count"] = members.count()
        if members.count() > 0:
            member = members.first()
            context["datas"] = SCDataSerializer(SCData.objects.filter(system=member.system, safety__gte=1).exclude(safety__isnull=True).exclude(safety__exact='').order_by('-id')[:10], many=True).data
            context["system"] = SCSystemSerializer(member.system, many=False).data
        return Response(context)


class SCAnalysisApi(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        context = {}
        members = SCMember.objects.filter(user=request.user, is_selected=True)
        context["selected_membership_count"] = members.count()
        if members.count() > 0:
            member = members.first()
            datas = SCData.objects.filter(system=member.system, safety__gte=1).exclude(safety__isnull=True).exclude(safety__exact='').order_by('-id')
            context["safety_average"] = round(datas.aggregate(Avg('safety'))["safety__avg"], 1)
            context["suspicious_average"] = round(datas.aggregate(Avg('suspicious'))["suspicious__avg"], 1)
            context["datas"] = SCDataSerializer(datas[:7], many=True).data
        return Response(context)
