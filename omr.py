import cv2
import csv
from datetime import datetime
import imutils
import numpy as np
import os
import pandas as pd

def omr_calculation():
    def get_main_countours(image):
        print("hiii")
        cnts = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
         
        cnts = imutils.grab_contours(cnts)
        docCnt = []
        if len(cnts) > 0:
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4:
                    docCnt.append(approx)
        return docCnt

    def get_bird_eye_view(image, cont):
        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = np.sum(pts,axis=1) #[[1, 2], [3, 4], [5, 6]] --> [3 7 11]
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            return rect
        def four_point_transform(image, pts):
            rect = order_points(pts)
            (tl, tr, br, bl) = rect
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype="float32")
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
            return warped

        warped = four_point_transform(image, cont.reshape(4, 2))  # numpy array 1d to 2d

        return warped

    def get_marks_section_2(image):
        def get_section_ans(inp):
            ans_marked = []
            temp1 = inp.copy()
            width = temp1.shape[1]
            height = temp1.shape[0]
            for i in range(5):
                found_index = []
                filled_ratios = []
                for j in range(4):
                    t = temp1[int(i * height / 5) + 10:int((i + 1) * height / 5) - 10,
                        int(j * width / 4):int((j + 1) * width / 4)]
                    erode_kernel = np.array([[1, 0, 1], [1, 0, 1], [1, 0, 1]]).astype(np.uint8)
                    t = cv2.erode(t, erode_kernel.astype(np.uint8), iterations=3)
                    filled_ratios.append(np.sum(t / 255.0) / (t.shape[0] * t.shape[1])) # normalization of slice
                if (sum(filled_ratios) == 0):  # all are empty
                    ans_marked.append(found_index)
                    continue
                filled_ratios_norm = filled_ratios / (sum(filled_ratios))   # normalization of 4 slice
                for i, ratio in enumerate(filled_ratios_norm):
                    if (ratio > 0.1):
                        found_index.append((i + 1))
                ans_marked.append(found_index)
            return ans_marked
        thresh = cv2.adaptiveThreshold(image[55:, :], 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 77, 10)
        thresh1 = thresh[:, 25:110]
        thresh2 = thresh[:, 165:-30]
        # cv2.imshow('Original Image', thresh)
        # cv2.waitKey(0)
        ans_marked = []
        ans_marked.extend(get_section_ans(thresh1))
        ans_marked.extend(get_section_ans(thresh2))
        return ans_marked

    def get_marks_section_1(image):
        def get_section_ans(inp):
            ans_marked = []
            temp1 = inp.copy()
            width = temp1.shape[1]
            height = temp1.shape[0]
            for i in range(2):
                found_index = []
                filled_ratios = []
                for j in range(4):
                    t = temp1[int(i * height / 2) + 5:int((i + 1) * height / 2) - 15,
                        int(j * width / 4):int((j + 1) * width / 4)]
                    erode_kernel = np.array([[1, 0, 1], [1, 0, 1], [1, 0, 1]]).astype(np.uint8)
                    t = cv2.erode(t, erode_kernel.astype(np.uint8), iterations=3)
                    filled_ratios.append(np.sum(t / 255.0) / (t.shape[0] * t.shape[1]))
                if (sum(filled_ratios) == 0):
                    ans_marked.append(found_index)
                    continue
                filled_ratios_norm = filled_ratios / (sum(filled_ratios))
                for i, ratio in enumerate(filled_ratios_norm):
                    if (ratio > 0.1 and filled_ratios[i] > 0.05):
                        found_index.append(i + 1)
                ans_marked.append(found_index)
            return ans_marked

        thresh = cv2.adaptiveThreshold(
            image[30:, :], 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 77, 10)

        thresh1 = thresh[:, 20:100]
        thresh2 = thresh[:, 160:240]
        thresh3 = thresh[:, 300:380]
        thresh4 = thresh[:, 435:515]
        thresh5 = thresh[:, 575:655]
        ans_marked = []
        ans_marked.extend(get_section_ans(thresh1))
        ans_marked.extend(get_section_ans(thresh2))
        ans_marked.extend(get_section_ans(thresh3))
        ans_marked.extend(get_section_ans(thresh4))
        ans_marked.extend(get_section_ans(thresh5))
        return ans_marked
    
    def main(image_path):
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)      
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edged = cv2.Canny(blurred, 75, 200)
        def display():
            # Display the original image
            cv2.imshow('Original Image', image)
            cv2.waitKey(0)

            # Display the grayscale image
            cv2.imshow('Grayscale Image', gray)
            cv2.waitKey(0)

            # Display the blurred image
            cv2.imshow('Blurred Image', blurred)
            cv2.waitKey(0)

            # Display the edge-detected image
            cv2.imshow('Edge-Detected Image', edged)
            cv2.waitKey(0)
        # display()
        main_contours = get_main_countours(edged)
        sections = []
        for cont in main_contours:
            warped = get_bird_eye_view(blurred, cont)
            if (warped.shape[0] < 50):  # for height 50+
                continue
            sections.append(warped)
        ans_marked_section_1 = get_marks_section_2(sections[2])
        ans_marked_section_2 = get_marks_section_1(sections[1])
        ans_marked = []
        ans_marked.extend(ans_marked_section_1)
        ans_marked.extend(ans_marked_section_2)
        return {
            "ans_marked": ans_marked
        }

    total_img = os.listdir("static/omr_sheets/")
    marklist = []
    csv_file = os.listdir("static/answer_sheet")
    csv_path = "static/answer_sheet/" + str(csv_file[0])
    for i in total_img:
        FILE_PATH = os.path.join(('static/omr_sheets/'), str(i))
        df = pd.read_csv(csv_path)
        answer = [list(map(int, str(x).split(','))) for x in df.answer]
        marks = df.marks.to_list()
        values = main(FILE_PATH)
        ansmarked = values["ans_marked"]
        def display2():
            print("Correct Answer")
            print(answer)

            # print(marks)
            print("Ans Marked")
            print(ansmarked)
        def cal1():
            score = 0
            curr = -1
            for q, r in zip(ansmarked, answer):
                curr = curr + 1
                if len(q) == 0:
                    continue
                else:
                    if (len(q) == len(r)):          # if  attemting multiple answer
                        for c in range(len(q)):
                            if (ansmarked[curr][c] != answer[curr][c]):
                                break
                            if(c==len(q)-1):   # if all answers are correct loop reched till end to avoid multiple adding of score for multiple correct
                                score = score + marks[curr]
            print(score)
            os.remove(FILE_PATH)
            return score
        score = cal1()         
        marklist.append(score)
    os.remove(csv_path) 
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"ans_{timestamp}.csv"
    filepath = os.path.join('static/result/', filename)
    with open(filepath, 'w', newline='') as file:
        csvwriter = csv.writer(file)
        fields = ['Score']
        csvwriter.writerow(fields)
        for i in marklist:
            csvwriter.writerow([i])
    return marklist,filepath