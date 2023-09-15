import os
import pandas as pd
import time
import shutil
example_dir = './data/'
dataframes=[]
_files=[]
_mistakes=[]
_notifications=[]
#сбор названий файлов из директории
with os.scandir(example_dir) as files:
    for file in files:
        filename, file_extension = os.path.splitext(file.name)
        if file_extension==".csv":
            _files.append(filename)
for x in _files:
    #чтение информации, и удаление пустых строк или столбцов
    ODS1=pd.read_csv('data/'+x+'.csv',encoding='cp1251')
    ODS1=ODS1.dropna(axis=0,how="all")
    ODS1=ODS1.dropna(axis=1,how="all")
    #защита от неправильно введённой инормации
    if ODS1.shape[1]!=5:
        print("В таблице неверное количество столбцов")
        raise SystemExit
    if ODS1.isnull().any().any():
        print("В таблице отсутствуют значения")
        raise SystemExit
    datatype=ODS1.dtypes
    if datatype.iloc[0]!="int64":
        _mistakes.append("В первом столбце должны быть только целые числа")
    if datatype.iloc[4]!="int64" and datatype.iloc[4]!="float64":
        _mistakes.append("В пятом столбце должны быть только числа")
    if len(_mistakes)>0:
        for item in _mistakes:
            print(item)
        raise SystemExit
    znach=ODS1.iloc[:,2].unique()
    for item in znach:
        if item.lower()!="активы" and item.lower()!="пассивы" and item.lower()!="чистая прибыль" and item.lower()!="выручка":
            _mistakes.append("Неподходящее значение в третьем столбце")
            break
    znach=ODS1.iloc[:,1]
    for item in znach:
        try:
            valid_date = time.strptime(item, '%m.%d.%y')
        except ValueError:
            print('Неверная дата')
            raise SystemExit
    #проверка идентичности дат
    if ODS1.iloc[:,1].nunique()>1:
            _mistakes.append('В таблице присутствуют разные даты')
    if len(_mistakes)>0:
        for item in _mistakes:
            print(item)
        raise SystemExit
    #чтение информации из DWH
    ODS2=pd.read_csv('rezult_data/result.csv',encoding='cp1251')
    #проверка на уникальность
    ODS=pd.concat([ODS1,ODS2])
    if len(ODS[ODS.iloc[:,0:4].duplicated()])>0:
        print("В таблице присутствуют неуникальные элементы")
        raise SystemExit
    #проверка на точность финансовых данных
    df=ODS1.iloc[:,[0,1]].drop_duplicates()
    for i in range(df.shape[0]):
        df1=ODS1.loc[((ODS1.iloc[:,0] == df.iloc[i,0]) & (ODS1.iloc[:,1] == df.iloc[i,1]))]
        is_active=False
        active=0
        is_passive=False
        passive=0
        is_revenue=False
        revenue=0
        is_profit=False
        profit=0
        for j in range(df1.shape[0]):
            match df1.iloc[j,2].lower():
                case 'активы':
                    if is_active:
                        if active!=df1.iloc[j,4]:
                            print ("Активы в разных отчётах отличаются друг от друга")
                            raise SystemExit
                        else:
                            active=df1.iloc[j,4]
                        if is_passive:
                            if passive!=active:
                                print("Активы не равны пассивам")
                                raise SystemExit
                    else:
                        if is_passive:
                            if passive!=df1.iloc[j,4]:
                                print ("Активы не равны пассивам")
                                raise SystemExit
                        is_active=True
                        active=df1.iloc[j,4]
                    if not ODS2.empty:
                        df2=ODS2.loc[((ODS2.iloc[:,0] == df1.iloc[j,0]) & (ODS2.iloc[:,1] == df1.iloc[j,1]) & ((ODS2.iloc[:,2].str.lower() == 'активы')| (ODS2.iloc[:,2].str.lower() == 'пассивы')))]
                        if not df2.empty:
                            for k in range(df2.shape[0]):
                                if df2.iloc[k,2].lower()=="активы":
                                    if df2.iloc[k,4]!=active:
                                        print("Активы в разных отчётах отличаются друг от друга")
                                        raise SystemExit
                                else:
                                    if df2.iloc[k,4]!=active:
                                        print("Активы не равны пассивам")
                                        raise SystemExit
                case 'пассивы':
                    if is_passive:
                        if passive!=df1.iloc[j,4]:
                            print ("Пассивы в разных отчётах отличаются друг от друга")
                            raise SystemExit
                        else:
                            passive=df1.iloc[j,4]
                        if is_active:
                            if active!=passive:
                                print("Активы не равны пассивам")
                                raise SystemExit
                    else:
                        if is_active:
                            if active!=df1.iloc[j,4]:
                                print ("Активы не равны пассивам")
                                raise SystemExit
                        is_passive=True
                        passive=df1.iloc[j,4]
                    if not ODS2.empty:
                        df2=ODS2.loc[((ODS2.iloc[:,0] == df1.iloc[j,0]) & (ODS2.iloc[:,1] == df1.iloc[j,1]) & ((ODS2.iloc[:,2].str.lower() == 'активы')| (ODS2.iloc[:,2].str.lower() == 'пассивы')))]
                        if not df2.empty:
                            for k in range(df2.shape[0]):
                                if df2.iloc[k,2].lower()=="Пассивы":
                                    if df2.iloc[k,4]!=passive:
                                        print("Пассивы в разных отчётах отличаются друг от друга")
                                        raise SystemExit
                                else:
                                    if df2.iloc[k,4]!=passive:
                                        print("Активы не равны пассивам")
                                        raise SystemExit
                case 'чистая прибыль':
                    if is_profit:
                        if profit!=df1.iloc[j,4]:
                            print ("Чистая прибыль в разных отчётах отличается друг от друга")
                            raise SystemExit
                        else:
                            profit=df1.iloc[j,4]
                        if is_revenue:
                            if profit>=revenue:
                                print("Чистая прибыль больше выручки")
                                raise SystemExit
                            else:##проверка на финансовые уведомления
                                if float(profit)/float(revenue)*100>50:
                                    print('ROS выше 50 процентов в компании с номером '+str(df1.iloc[0,0]))
                        df2=ODS2.loc[((ODS2.iloc[:,0] == df1.iloc[j,0]) & (ODS2.iloc[:,1] == df1.iloc[j,1]) & ((ODS2.iloc[:,2].str.lower() == 'чистая прибыль')))]
                        if df2.iloc[:,4].max()<df1.iloc[j,4]:#проверка на финансовые уведомления
                            print("Максимальная чистая прибыль в компании "+str(df1.iloc[0,0])+" равная "+str(df1.iloc[j,4]))
                    else:
                        if is_revenue:
                            if revenue<=df1.iloc[j,4]:
                                print ("Чистая прибыль больше выручки")
                                raise SystemExit
                            else:#проверка на финансовые уведомления
                                if float(df1.iloc[j,4])/float(revenue)*100>50:
                                    print('ROS выше 50 процентов в компании с номером '+str(df1.iloc[0,0]))
                        is_profit=True
                        profit=df1.iloc[j,4]#Финансовое уведомление
                        print("Максимальная чистая прибыль в компании "+str(df1.iloc[0,0])+" равная "+str(df1.iloc[j,4]))
                    if not ODS2.empty:
                        df2=ODS2.loc[((ODS2.iloc[:,0] == df1.iloc[j,0]) & (ODS2.iloc[:,1] == df1.iloc[j,1]) & ((ODS2.iloc[:,2].str.lower() == 'чистая прибыль')| (ODS2.iloc[:,2].str.lower() == 'выручка')))]
                        if not df2.empty:
                            for k in range(df2.shape[0]):
                                if df2.iloc[k,2].lower()=="чистая прибыль":
                                    if df2.iloc[k,4]!=profit:
                                        print("Чистая прибыль в разных отчётах отличается друг от друга")
                                        raise SystemExit
                                else:
                                    if df2.iloc[k,4]<=profit:
                                        print("Чистая прибыль больше выручки")
                                        raise SystemExit
                                    else:#проверка на финансовые уведомления
                                        if float(profit)/float(df2.iloc[k,4])*100>50:
                                            print('ROS выше 50 процентов в компании с номером '+str(df1.iloc[0,0]))
                case 'выручка':
                    if is_revenue:
                        if revenue!=df1.iloc[j,4]:
                            print ("Выручка в разных отчётах отличаются друг от друга")
                            raise SystemExit
                        else:
                            revenue=df1.iloc[j,4]
                        if is_profit:
                            if revenue<=profit:
                                print("Чистая прибыль больше выручки")
                                raise SystemExit
                            else:#проверка на финансовые уведомления
                                if float(profit)/float(revenue)*100>50:
                                    print('ROS выше 50 процентов в компании с номером '+str(df1.iloc[0,0]))
                    else:
                        if is_profit:
                            if profit>=df1.iloc[j,4]:
                                print ("Чистая прибыль больше выручки")
                                raise SystemExit
                            else:#проверка на финансовые уведомления
                                if float(profit)/float(df1.iloc[j,4])*100>50:
                                    print('ROS выше 50 процентов в компании с номером '+str(df1.iloc[0,0]))
                        is_revenue=True
                        revenue=df1.iloc[j,4]
                    if not ODS2.empty:
                        df2=ODS2.loc[((ODS2.iloc[:,0] == df1.iloc[j,0]) & (ODS2.iloc[:,1] == df1.iloc[j,1]) & ((ODS2.iloc[:,2].str.lower() == 'чистая прибыль')| (ODS2.iloc[:,2].str.lower() == 'выручка')))]
                        if not df2.empty:
                            for k in range(df2.shape[0]):
                                if df2.iloc[k,2].lower()=="выручка":
                                    if df2.iloc[k,4]!=revenue:
                                        print("Выручка в разных отчётах отличается друг от друга")
                                        raise SystemExit
                                else:
                                    if df2.iloc[k,4]>=revenue:
                                        print("Чистая прибыль больше выручки")
                                        raise SystemExit
                                    else:
                                        if float(df2.iloc[k,4])/float(revenue)*100>50:#проверка на финансовые уведомления
                                            print('ROS выше 50 процентов в компании с номером '+str(df1.iloc[0,0]))
        if (not is_active) or (not is_passive) or (not is_revenue) or (not is_profit) :#проверка на уведомления по полноте данных
            print('Значения есть не по всем показателям, по компании под номером ' + str(df1.iloc[0,0]))
    unique_company_list=ODS1.iloc[:,0].unique()
    for item in unique_company_list:#проверка на уведомления, о появлении новых компаний
        if ODS2.iloc[:,0].isin([item]).any()==False:
            print('Новая компания с номером '+str(item))
    print(x+'.csv'+' успешно загруженна')
    ODS1.to_csv('rezult_data/result.csv',encoding='cp1251',mode='a', index= False , header= False )



