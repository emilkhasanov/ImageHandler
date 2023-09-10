import PIL
import cv2 as cv
from PIL import Image
import numpy as np
import yaml
import sqlite3
import json
import matplotlib.pyplot as plt

class yaml_worker(): # вычитка данных из файла
    def yaml_reader(self, input_file):
        with open(input_file, "r") as file:
            data = yaml.safe_load(file)
            std = data['std']
            dispersion = data['dispersion']
            position = data['position']
            return [std, dispersion, position]

class dev_disp_calculator(): # расчет статистики отклонения и дисперсии
    def statistics(self, data_input):
        st_dev = data_input
        st_dev_out = np.std(st_dev)
        disp = np.var(data_input)
        disp_out = np.average(disp)
        return [round(st_dev_out), round(disp_out)]

class working_with_images(): # работа с изображениями
    def image_worker(self, image_input): # функция расчета центральных координат
        # change it with your absolute path for the image
        image = cv.imread(image_input)
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        blur = cv.GaussianBlur(gray, (5, 5),
                               cv.BORDER_DEFAULT)
        ret, thresh = cv.threshold(blur, 200, 255,
                                   cv.THRESH_BINARY_INV)
        cv.imwrite("thresh.png", thresh)

        contours, hierarchies = cv.findContours(
            thresh, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

        blank = np.zeros(thresh.shape[:2],
                         dtype='uint8')

        cv.drawContours(blank, contours, -1,
                        (255, 0, 0), 1)

        cv.imwrite("photo_2.png", blank)

        for i in contours:
            M = cv.moments(i)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                cv.drawContours(image, [i], -1, (0, 255, 0), 2)
                cv.circle(image, (cx, cy), 7, (0, 0, 255), -1)
                cv.putText(image, "center", (cx - 20, cy - 20),
                           cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            print(f"x: {cx} y: {cy}")
            # координаты начала отсчета
            x_zero = cx
            y_zero = cy
        cv.imwrite("image_2.png", image)

        image = Image.open(image_input)
        mask=image.convert("L")
        th=150 # the value has to be adjusted for an image of interest
        mask = mask.point(lambda i: i < th and 255)
        mask.save('result.png')

        # change it with your absolute path for the image
        image = cv.imread("result.png")
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        blur = cv.GaussianBlur(gray, (5, 5),
                               cv.BORDER_DEFAULT)
        ret, thresh = cv.threshold(blur, 200, 255,
                                   cv.THRESH_BINARY_INV)
        cv.imwrite("thresh.png", thresh)

        contours, hierarchies = cv.findContours(
            thresh, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

        blank = np.zeros(thresh.shape[:2],
                         dtype='uint8')

        cv.drawContours(blank, contours, -1,
                        (255, 0, 0), 1)

        cv.imwrite("Contours.png", blank)

        for i in contours:
            M = cv.moments(i)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                cv.drawContours(image, [i], -1, (0, 255, 0), 2)
                cv.circle(image, (cx, cy), 7, (0, 0, 255), -1)
                cv.putText(image, "center", (cx - 20, cy - 20),
                           cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            print(f"x: {cx} y: {cy}")
            # координаты центра пятна
            x = cx - x_zero
            y = cy - y_zero
        cv.imwrite("image.png", image)

        return [x, y, x_zero, y_zero]

    def coordinates_from_contour(self, image): # координаты окружности контура пятна
        image = PIL.Image.open(image)
        f = image.load()
        color = (255)
        PixelCoordinates = []
        for x in range(0, image.size[0]):
            for y in range(0, image.size[1]):
                if f[x, y] == color:
                    PixelCoordinates.append([x, y])
        return PixelCoordinates

    def create_proection(self, PixelCoordinates, coord): # создание изображения проекции и выгрузка координат в текстовый файл
        plt.figure()
        ax = plt.gca()
        ax.spines['left'].set_position('center')
        ax.spines['bottom'].set_position('center')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        xdata = []
        ydata = []
        for i in range(0, len(PixelCoordinates)):
            coordinate = PixelCoordinates[i]
            xdata.append(coordinate[0] - coord[2])
            ydata.append(coordinate[1] - coord[3])
        xdata.append(coord[0])
        ydata.append(coord[1])
        plt.scatter(xdata, ydata, c='gray', s=1)
        plt.savefig('proection.png', bbox_inches='tight')
        with open('proection.txt', 'w') as file:
            file.write(str(f'X coordinates  {xdata}\n'))
            file.write(str(f'Y coordinates  {ydata}\n'))

class data_base_worker(): # работа с бд
    def data_base_writer(self, STD, Dispersion, Position_X, Position_Y): # запись данных в бд
        # Устанавливаем соединение с базой данных
        connection = sqlite3.connect('test_db.db')
        cursor = connection.cursor()

        # Создаем таблицу Datas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Datas (
        id INTEGER PRIMARY KEY,
        STD INTEGER NOT NULL,
        Dispersion INTEGER NOT NULL,
        Position_X INTEGER NOT NULL,
        Position_Y INTEGER NOT NULL
        )
        ''')
        cursor.execute('INSERT INTO Datas (STD, Dispersion, Position_X, Position_Y) VALUES (?, ?, ?, ?)', (STD, Dispersion, Position_X, Position_Y))

        # Сохраняем изменения и закрываем соединение
        connection.commit()
        connection.close()

    def data_base_reader(self): # чтение данных из бд
        # Устанавливаем соединение с базой данных
        connection = sqlite3.connect('test_db.db')
        cursor = connection.cursor()

        # Выбираем всех пользователей
        cursor.execute('SELECT * FROM Datas')
        Datas = cursor.fetchall()
        all_datas = []
        # Выводим результаты
        for data in Datas:
            all_datas.append(data)
        connection.close()
        return all_datas

    def data_base_delete(self): # очистка бд при необходимости
        # Устанавливаем соединение с базой данных
        connection = sqlite3.connect('test_db.db')
        cursor = connection.cursor()
        cursor.execute("delete from Datas where id>(?)", (0,))
        connection.commit()
        connection.close()

class assertions(): # проверка отклонения, дисперсии и координат относительно ожидаемого результата
    def std_assert(self, ex_res_std,act_res_std): # проверка отклонения
        if ex_res_std == act_res_std:
            assertion_std = 'valid_std'
        else:
            assertion_std = 'invalid_std'

        # Data to be written
        results = {'std_assert' : {
            "ex_res_std": ex_res_std,
            "act_res_std": act_res_std,
            "assertion_std": assertion_std,
        }}
        all_json.json_worker(results)

    def disp_assert(self, ex_res_disp, act_res_disp): # проверка дисперсии
        if ex_res_disp == act_res_disp:
            assertion_disp = 'valid_disp'
        else:
            assertion_disp = 'invalid_disp'

        # Data to be written
        results = {'disp_assert' : {
            "ex_res_disp": ex_res_disp,
            "act_res_disp": act_res_disp,
            "assertion_disp": assertion_disp,
        }}
        all_json.json_worker(results)

    def coord_assert(self, ex_coord,act_coord): # проверка координат
        if ex_coord == act_coord:
            assertion_coord = 'valid_coord'
        else:
            assertion_coord = 'invalid_coord'

        # Data to be written
        results = {"coord_assert" : {
            "ex_coord": ex_coord,
            "act_coord": act_coord,
            "assertion_coord": assertion_coord
        }}
        all_json.json_worker(results)

class json_worker(): # запись данных в файл
    def json_worker(self, results): # добавление записи в файл
        # Serializing json
        json_object = json.dumps(results, indent=4)
        # Writing to sample.json
        with open("Output_data.json", "a") as outfile:
            outfile.write(json_object)
            outfile.write("\n")

    def clear_json(self): # очистка файла перед началом работы
        open("Output_data.json","w").close()

if __name__ == "__main__":
    all_yaml = yaml_worker()
    all_statistics = dev_disp_calculator()
    all_images = working_with_images()
    all_data_base = data_base_worker()
    all_assertions = assertions()
    all_json = json_worker()

    # all_data_base.data_base_delete() #если необходимо очистить базу данных

    ex_res = all_yaml.yaml_reader('Input_data.yml') #чтение входных данных
    coordinates = all_images.image_worker('photo.png') #получение координат центра пятна
    all_datas = all_data_base.data_base_reader() #вычитка изначальных данных для последующих расчетов статистики
    all_coordinates = []
    for data in all_datas:
        all_coordinates.append(data[3] * data[4])
    all_coordinates.append(coordinates[0] * coordinates[1]) #вычитка и перемножение всех координат из бд (перемножение для дальнейшей оценки отклонения
    std_disp = all_statistics.statistics(all_coordinates) #расчет статистики
    all_data_base.data_base_writer(std_disp[0],std_disp[1],coordinates[0],coordinates[1])#запись новых данных в бд
    all_json.clear_json() #очистка файла перед выводом проверки
    all_assertions.std_assert(ex_res[0], std_disp[0]) # проверка отклонения
    all_assertions.disp_assert(ex_res[1], std_disp[1]) # проверка дисперсии
    all_assertions.coord_assert(ex_res[2], coordinates) # проверка координат
    all_images.create_proection(all_images.coordinates_from_contour('Contours.png'), coordinates) # вывод проекции в изображение и запись координат в текстовый файл


