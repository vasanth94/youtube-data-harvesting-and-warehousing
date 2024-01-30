
from googleapiclient.discovery import build
from pymongo import MongoClient
import psycopg2
import pandas as pd
import streamlit as st


# API KEY GETTING

def Api_connect():
    Api_Id= "AIzaSyApwCtO7iAATd5krZ9gAz3-dsChZLDqWSI"
    api_service_name="youtube"
    api_version="v3"
    youtube= build( api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube=Api_connect()


#GETTING INFORMATION FROM CHANNEL
def get_channel_info(channel_id):
    request=youtube.channels().list(                                                            
                    part="snippet,contentDetails,statistics",
                    id=channel_id)
    
    response = request.execute()

    for i in response['items']: 
        data=dict(channel_Name=i["snippet"]["title"],
                    channel_id=i["id"],
                    subscribers=i["statistics"]["subscriberCount"],                  
                    views=i["statistics"]["viewCount"],
                    Total_videos=i["statistics"]["videoCount"],
                    channel_description=i["snippet"]["description"],
                    playlist_id=i["contentDetails"]["relatedPlaylists"]["uploads"] )
        
    return data


def get_videos_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id, 
                                        part='contentDetails').execute()
    playlist_Id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


    next_page_token=None

    while True: 
            response1=youtube.playlistItems().list(
                                                part='snippet',
                                                playlistId=playlist_Id,
                                                maxResults=50,
                                                pageToken=next_page_token).execute()
            for i in range(len(response1['items'])): 
                video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
            next_page_token=response1.get('nextPageToken')


            if next_page_token is None:
                break
    return video_ids


#video full information
def get_video_info(video_Ids):
    video_data=[]
    for video_id in video_Ids:
        request=youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
        ) 
        response=request.execute()


        for item in response["items"]:
            data=dict(channel_Name=item['snippet']['channelTitle'],
                    channel_id=item['snippet']['channelId'],
                    video_Id=item['id'],
                    Title=item['snippet']['title'],
                    Tags=item['snippet'].get('Tags'),
                    Thumbnail=item['snippet']['thumbnails']['default']['url'],
                    Description=item['snippet'].get('description'),
                    Published_Date=item['snippet']['publishedAt'],
                    Duration=item['contentDetails']['duration'],
                    Views=item['statistics'].get('viewCount'),
                    Likes=item['statistics'].get('likeCount'),
                    Comments=item['statistics'].get('commentCount'),
                    Favourite_Count=item['statistics']['favoriteCount'],
                    Definition=item['contentDetails']['definition'],
                    Caption_Status=item['contentDetails']['caption'])
                    
            video_data.append(data)
    return video_data


   #COMMENT INFORMATION
def  get_comment_info( video_Ids):

    Comment_data=[]

    try:
        for video_id in video_Ids:
            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50)
        
            response=request.execute()


            for item in response['items']:
                data=dict(comment_Id=item['snippet']['topLevelComment']['id'],
                        video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
                        Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_Published=item['snippet']['topLevelComment']['snippet']['publishedAt'])
                Comment_data.append(data)

    except:
        pass
    return Comment_data


#GET_PLAYLIST_INFO
def get_playlist_details(channel_id):
        next_page_token=None
        All_data=[]
        while True:
                request=youtube.playlists().list(  
                        part='snippet,contentDetails',
                        channelId=channel_id,
                        maxResults=50,
                        pageToken=next_page_token)
        
                response=request.execute()

                for item in response['items']:
                        data=dict(Playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                channel_Id=item['snippet']['channelId'],
                                channel_Name=item['snippet']['channelTitle'],
                                PublishedAt=item['snippet']['publishedAt'],
                                Video_Count=item['contentDetails']['itemCount']
                                )
                        All_data.append(data)


                next_page_token=response.get('nextPageToken')
                if next_page_token is None:
                        break
        return All_data

#EXPORT TO MONGODB

client= MongoClient("mongodb://localhost:27017")
db=client["youtube_data"]

def channel_details(channel_id):
  ch_details=get_channel_info(channel_id)
  pl_details=get_playlist_details(channel_id)
  vi_ids=get_videos_ids(channel_id)
  vi_details=get_video_info(vi_ids)
  com_details=get_comment_info(vi_ids)


  coll1=db["channel_details"]  # collections
  coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,
                    "video_information":vi_details,"comment_information":com_details})
  
  return "insert successfully"

#TABLE CREATION FOR CHANNEL INFO
def channels_table():
    mydb=psycopg2.connect(host="localhost",
                            user="postgres",
                            password="ananya14",
                            database="youtube_data",
                            port="5432")                      
    cursor=mydb.cursor()

    drop_query='''drop table if exists channels'''
    cursor.execute(drop_query)
    mydb.commit()

    try:
            create_query='''create table if not exists channels(Channel_Name varchar(100),Channel_Id varchar(80) primary key,Subscribers bigint,Views bigint,Total_Videos int,Channel_Description text,Playlist_Id varchar(80))'''
            cursor.execute(create_query)
            mydb.commit()
    except:
            print("Channels table already created")

    ch_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
            ch_list.append(ch_data["channel_information"])
    df=pd.DataFrame(ch_list)

    for index,row in df.iterrows():
            insert_query='''insert into channels(Channel_Name,Channel_Id,Subscribers,Views,Total_Videos,Channel_Description,Playlist_Id) values(%s,%s,%s,%s,%s,%s,%s)'''
            values=(row["channel_Name"],row["channel_id"],row["subscribers"],row["views"],row["Total_videos"],row["channel_description"],row["playlist_id"])

            try:
                cursor.execute(insert_query,values)
                mydb.commit()
            except:
                print("Channel Values are already inserted")

    return df
    
# to create playlist
def playlist_table():
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="ananya14",
                        database="youtube_data",
                        port="5432")                      
    cursor=mydb.cursor()

    drop_query='''drop table if exists playlists'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists playlists(playlist_id varchar(100) primary key,
                                                         title varchar(100),
                                                         channel_id varchar(100),
                                                         channel_name varchar(100),
                                                         publishedat timestamp,
                                                         video_count int
                                                         )'''
    
    cursor.execute(create_query)
    mydb.commit()

    pl_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])
    df1=pd.DataFrame(pl_list)

    for index,row in df1.iterrows():
            insert_query='''insert into playlists(playlist_id,title,channel_id,channel_name,publishedat,video_count) values(%s,%s,%s,%s,%s,%s)'''
            values=(row["Playlist_Id"],row["Title"],row["channel_Id"],row["channel_Name"],row["PublishedAt"],row["Video_Count"])
            cursor.execute(insert_query,values)
            mydb.commit()


# sql table creation for videos


def videos_table():
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="ananya14",
                        database="youtube_data",
                        port="5432")                      
    cursor=mydb.cursor()

    drop_query='''drop table if exists videos'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists videos(Channel_Name varchar(100),Channel_Id varchar(100),Video_Id varchar(100) primary key,Title varchar(200),Tags text,Thumbnail varchar(200),Description text,Publish_Date timestamp,Duration interval,Views bigint,Likes bigint,Comments bigint,Favorite_Count bigint,Definition varchar(20),Caption_Status varchar(100))'''
     
    cursor.execute(create_query)
    mydb.commit()


    vi_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2=pd.DataFrame(vi_list)

    for index,row in df2.iterrows():
            insert_query='''insert into videos(Channel_Name,Channel_Id,Video_Id,Title,Tags,Thumbnail,Description,Publish_Date,Duration,Views,Likes,Comments,Favorite_Count,Definition,Caption_Status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

            values=(row["channel_Name"],row["channel_id"],row["video_Id"],row["Title"],row["Tags"],row["Thumbnail"],row["Description"],row["Published_Date"],row["Duration"],row["Views"],row["Likes"],
                    row["Comments"],row["Favourite_Count"],row["Definition"],row["Caption_Status"])

            cursor.execute(insert_query,values)
            mydb.commit()

    
# SQL TABLE FOR COMMENTS

def comments_table():
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="ananya14",
                        database="youtube_data",
                        port="5432")                      
    cursor=mydb.cursor()

    drop_query='''drop table if exists comments'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists comments(Comment_Id varchar(100)primary key,
                                                        Video_Id varchar(100),
                                                        Comment_Text text,
                                                        Comment_Author varchar(150),
                                                        Comment_Published timestamp)'''

    cursor.execute(create_query)
    mydb.commit()

    com_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3=pd.DataFrame(com_list)

    for index,row in df3.iterrows():
            insert_query='''insert into comments(Comment_Id,Video_Id,Comment_text,Comment_Author,Comment_Published) values(%s,%s,%s,%s,%s)'''

            values=(row["comment_Id"],row["video_Id"],row["Comment_Text"],row["Comment_Author"],row["Comment_Published"])

            cursor.execute(insert_query,values)
            mydb.commit()



def tables():
    channels_table()
    playlist_table()
    videos_table()
    comments_table()

    return "Tables Created Successfully"

def show_channels_table():
    ch_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)
    return df

def show_playlists_table():
    pl_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])
    df1=st.dataframe(pl_list)

    return df1

def show_videos_table():
    vi_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2=st.dataframe(vi_list)
    return df2

def show_comments_table():
    com_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3=st.dataframe(com_list)

    return df3


# STREAMLIT PORTION


with st.sidebar:
    st.title(":green[Youtube Data Harvesting and Warehousing]")
    st.header("Skill extract")
    st.caption("Python Scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data Management using MongoDB and SQL")

channel_id=st.text_input("Enter Channel Id")

if st.button("Collect and Store Data"):
    ch_ids=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["channel_id"])

    if channel_id in ch_ids:
        st.success("Channel Details of the given channel id already exists")

    else:
        insert=channel_details(channel_id)
        st.success(insert)

if st.button("Migrate to SQL"):
    Table=tables()
    st.success(Table)

show_table=st.radio("Select to view the table", ("Channels", "Playlists", "Videos", "Comments"))

if show_table=="Channels":
    show_channels_table()
    
elif show_table=="Playlists":
    show_playlists_table()
    
elif show_table=="Videos":
    show_videos_table()
   
elif show_table=="Comments":
    show_comments_table()
    


#CONNECT TO SQL

mydb=psycopg2.connect(host="localhost",
                    user="postgres",
                    password="ananya14",
                    database="youtube_data",
                    port="5432")                      
cursor=mydb.cursor()

question=st.selectbox("Choose the Question",("1.What are the names of all the videos and their corresponding channels?",
                                             "2. Which channels have the most number of videos, and how many videos do they have?",
                                             "3. What are the top 10 most viewed videos and their respective channels?",
                                             "4. How many comments were made on each video, and what are their corresponding video names?",
                                             "5. Which videos have the highest number of likes, and what are their corresponding channel names?",
                                             "6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
                                             "7. What is the total number of views for each channel, and what are their corresponding channel names?",
                                             "8. What are the names of all the channels that have published videos in the year 2022?",
                                             "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                             "10. Which videos have the highest number of comments, and what are their corresponding channel names?"))

mydb=psycopg2.connect(host="localhost",
                    user="postgres",
                    password="ananya14",
                    database="youtube_data",
                    port="5432")                      
cursor=mydb.cursor()

if question== "1.What are the names of all the videos and their corresponding channels?":
    query1='''select title as videos,channel_name as channelname from videos'''
    cursor.execute(query1)
    mydb.commit()
    t1=cursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)
elif question=="2. Which channels have the most number of videos, and how many videos do they have?":
    query2='''select channel_name as channelname,total_videos as no_videos from channels order by total_videos desc'''
    cursor.execute(query2)
    mydb.commit()
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2, columns=["channel name","no of videos"])
    st.write(df2)
elif question=="3. What are the top 10 most viewed videos and their respective channels?":
    query3='''select views as views,channel_name as channelname,title as videotitle from videos where views is not null order by views limit 10'''
    cursor.execute(query3)
    mydb.commit()
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3, columns = ["views","channel name","videotitle"])
    st.write(df3)
elif question=="4. How many comments were made on each video, and what are their corresponding video names?":
    query4="select Comments as No_comments ,Title as VideoTitle from videos where Comments is not null;"
    cursor.execute(query4)
    mydb.commit()
    t4=cursor.fetchall()
    df4=pd.DataFrame(t4, columns=["No Of Comments", "videotitle"])
    st.write(df4)
elif question=="5. Which videos have the highest number of likes, and what are their corresponding channel names?":
    query5='''select Title as VideoTitle, Channel_Name as ChannelName, Likes as LikesCount from videos where Likes is not null order by Likes desc;'''
    cursor.execute(query5)
    mydb.commit()
    t5=cursor.fetchall()
    df5=pd.DataFrame(t5, columns=["videotitle","channel name","like count"])
    st.write(df5)
elif question=="6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
    query6='''select Likes as likeCount,Title as VideoTitle from videos;'''
    cursor.execute(query6)
    mydb.commit()
    t6 = cursor.fetchall()
    df6=pd.DataFrame(t6, columns=["like count","videotitle"])
    st.write(df6)
elif question=="7. What is the total number of views for each channel, and what are their corresponding channel names?":
    query7="select Channel_Name as ChannelName, Views as Channelviews from channels;"
    cursor.execute(query7)
    mydb.commit()
    t7=cursor.fetchall()
    df7=pd.DataFrame(t7, columns=["channel name","total views"])
    st.write(df7)
elif question=="8. What are the names of all the channels that have published videos in the year 2022?":
    query8='''select Title as Video_Title, Published_Date as VideoRelease, Channel_Name as ChannelName from videos where extract(year from Published_Date) = 2022;'''
    cursor.execute(query8)
    mydb.commit()
    t8=cursor.fetchall()
    df8=pd.DataFrame(t8,columns=["Name", "Video Publised On", "ChannelName"])
    st.write(df8)
elif question=="9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
    query9='''SELECT Channel_Name as ChannelName, AVG(Duration) AS average_duration FROM videos GROUP BY Channel_Name;'''
    cursor.execute(query9)
    mydb.commit()
    t9=cursor.fetchall()
    df9=pd.DataFrame(t9, columns=['ChannelTitle', 'Average Duration'])
    T9=[]
    for index, row in df9.iterrows():
        channel_title = row['ChannelTitle']
        average_duration = row['Average Duration']
        average_duration_str = str(average_duration)
        T9.append({"Channel Title": channel_title ,  "Average Duration": average_duration_str})
    df1=pd.DataFrame(t9)   
    st.write(pd.DataFrame(T9))
elif question=="10. Which videos have the highest number of comments, and what are their corresponding channel names?":
    query10='''select Title as VideoTitle, Channel_Name as ChannelName, Comments as Comments from videos where Comments is not null order by Comments desc;'''
    cursor.execute(query10)
    mydb.commit()
    t10=cursor.fetchall()
    df10=pd.DataFrame(t10, columns=['videotitle', 'channel name', 'NO Of Comments'])
    st.write(df10)






        

                                    