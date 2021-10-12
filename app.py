import os
import sqlite3

from flask.wrappers import Request
from requests.api import get
# from typing import AwaitableGenerator, Text
import spotipy
import time
import datetime
import requests
import json
from flask import Flask, flash, redirect, render_template, url_for, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, register_check, login_check
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import config
from models import users, song_locations, songs, follow, made_playlists, db

GOOGLE_MAP_API_KEY = config.GOOGLE_MAP_API_KEY
SPOTIFY_CLIENT_SECRET =config.SPOTIFY_CLIENT_SECRET
SPOTIFY_CLIENT_ID = config.SPOTIFY_CLIENT_ID

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.secret_key = 'SOMETHING-RANDOM'
app.config['SESSION_COOKIE_NAME'] = 'session-id'

#database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
db.app = app

db.create_all()
print("table is created")

@app.route('/', methods = ['GET'])
@login_required
def index():
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')    
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    # マップ表示
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY
    pins = []
    songdata = []
    # print(session["user_id"])
    pins = db.session.query(song_locations).filter(song_locations.user_id == session["user_id"]).all()
    
    for pin in pins:
        # print(pin)
        song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})
        # print(pin.date)

    return render_template('index.html',user_id=session["user_id"] , GOOGLEMAPURL=googlemapURL ,Songdatas=songdata)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.pop("user_id", None)
    print("register")

    if request.method == "POST":
        username = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        nickname = request.form.get("username")
        
        used_email = db.session.query(users).filter(users.username == username).all()
        if used_email != []:
            print(used_email[0].username)
            print("is used username")

        # Ensure username, password, confirmation password, nickname was submitted
        if register_check(username, password, confirmation, nickname, used_email):
            # Insert user data
            
            new_user = users(username=username, hash=generate_password_hash(password), nickname=nickname)
            db.session.add(new_user)
            db.session.commit()

            users_row = db.session.query(users).filter(users.nickname == nickname).all()
            print(users_row[0].username)
            print("is new user username")

            # Ensure nickname exists and password is correct
            if not check_password_hash(users_row[0].hash, password):
                return render_template("register.html")

            session["user_id"] = users_row[0].id
            # Redirect user to home page
            return redirect("/")
        else:
            return render_template("register.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.pop("user_id", None)
    print("login")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("email")
        password = request.form.get("password")

        users_row = db.session.query(users).filter(users.username == username).all()
        if users_row != []:
            print(users_row[0].username)
            print("is login username")

        # Ensure username, password was submitted
        # Query database for nickname
        if login_check(username, password, users_row):
            # Ensure nickname exists and password is correct
            if not check_password_hash(users_row[0].hash, password):
                return render_template("login.html")

            # Remember which user has logged in
            session["user_id"] = users_row[0].id

            # Redirect user to home page
            return redirect("/")
        else:
            return render_template("login.html")
    # User reached route via GET (as by clicking a link or via redirect)
    else :
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.pop("user_id", None)
    
    # Redirect user to login form
    return redirect("/")



@app.route('/profile/<display_user_id>', methods = ['GET','POST'])
@login_required
def profile(display_user_id):
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')    
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))

    # ユーザの情報
    login_user_id = session["user_id"]
    track_ids = db.session.query(song_locations.track_id).filter(song_locations.user_id == display_user_id).all()
    username = db.session.query(users.username).filter(users.id == display_user_id).first()
    nickname = db.session.query(users.nickname).filter(users.id == display_user_id).first()
    print("login_user_id: ", end="")
    print(login_user_id)
    print("username: ", end="")
    print(username[0])
    print(nickname[0])

    # マップ表示
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY
    pins = []
    songdata = []
    pins = db.session.query(song_locations).filter(song_locations.user_id == display_user_id).all()
    
    for pin in pins:
        song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})
        print(pin.date)

    following_status = ""

    # 表示しているユーザーのフォロー情報
    display_user_id = int(display_user_id) # int型に統一
    if display_user_id == login_user_id:
        following_status = "myself"
    else:
        following = db.session.query(follow).filter(follow.follow_user_id == login_user_id, follow.followed_user_id == display_user_id).first()
        if following:
            following_status = "True"
        else:
            following_status = "False"
    
    # print("following: ", end="")
    # print(following)

    # フォローフォロワー数
    follow_user = db.session.query(follow).filter(follow.follow_user_id == display_user_id).all()
    if follow_user:
        follow_number = len(follow_user)
    else: 
        follow_number = 0

    followed_user = db.session.query(follow).filter(follow.followed_user_id == display_user_id).all()
    if followed_user:
        followed_number = len(followed_user)
    else:
        followed_number = 0

    songlists = []
    for track_id in track_ids:
        songlists.append(db.session.query(songs.track_name, songs.artist_name, songs.track_image, songs.spotify_url).filter(songs.track_id == track_id[0]).first())
    
    user_info = dict(id=display_user_id, username=username[0], following=following_status, follow_number=follow_number, followed_number=followed_number, songlists=songlists, nickname=nickname[0])
    if request.method == "GET":
        return render_template('profile.html', user_id=login_user_id ,user_info=user_info, GOOGLEMAPURL=googlemapURL ,Songdatas=songdata)
    if request.method == "POST":
        #makeplaylistにデータ渡す
        playlist_name = request.form['playlistname']
        return render_template('makeplaylist.html', data = songdata, name = playlist_name, user_id = session['user_id'])




@app.route('/follow', methods = ['POST'])
@login_required
# profile->follow->home
def following():
    operator = session["user_id"]
    operated = request.form.get("user_id")
    follow_or_cancell = request.form.get("follow_or_cancell")
    if operator != operated:
        if follow_or_cancell == "follow":
            new_follow = follow(follow_user_id=operator, followed_user_id=operated)
            db.session.add(new_follow)
            db.session.commit()
            print("follow", end=": ")
            print(operated)
            rows = db.session.query(follow).all()
            for row in rows:
                print(row.follow_user_id, end="->")
                print(row.followed_user_id)
        elif follow_or_cancell == "cancell":
            # 指定したデータを削除
            delete_follows = db.session.query(follow).filter_by(follow_user_id=operator, followed_user_id=operated).all()
            print(delete_follows)
            for delete_follow in delete_follows:
                db.session.delete(delete_follow)
            db.session.commit()
            print("cancell", end=": ")
            print(operated)
            rows = db.session.query(follow).all()
            for row in rows:
                print(row.follow_user_id, end="->")
                print(row.followed_user_id)
        else:
            print("error")
            return redirect("/")
        
        return redirect("/")
        
        # マップ表示
        # googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY
        # pins = []
        # songdata = []
        # display_user_id = operated
        # pins = db.session.query(song_locations).filter(song_locations.user_id == display_user_id).all()
        
        # for pin in pins:
        #     song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        #     songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        #     'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})
        #     print(pin.date)


        # user_info = dict(id=display_user_id, name="ma-")
        # return render_template('profile.html',login_user_id=session["user_id"] ,user_info=user_info, GOOGLEMAPURL=googlemapURL ,Songdatas=songdata)
        
    else:
        print("error")
        return redirect("/profile")
        # return render_template('profile.html') 

@app.route('/search', methods = ['GET'])
@login_required
def search():
    # #ユーザ検索
	# まずはログインユーザのもってるアーティストリストを出す。
    artistslist = []
    artistsdata = db.session.query(songs.artist_name, songs.track_image, songs.track_name).filter(songs.track_id == song_locations.track_id).filter(song_locations.user_id == session["user_id"]).all()   

    for artistdata in artistsdata:
        print(artistdata[0]) 
        # print(artistdata.track_name)
        print(artistdata[2])
        # print (artistname.replace("(","").replace(")","").replace("'",""))
        artistslist.append(artistdata[0])

    artist_info = []
    for artistdata in artistsdata:
        artist_info.append(artistdata)

    # newartistlist =[]
    # # print(artistslist.replace("(","").replace(")","").replace("'",""))
    # for artist in artistslist:
    #     artist = artist.replace("(","").replace(")","").replace("'","")
    #     print(artist)
    #     newartistlist.append({'artistname':artist})

    return render_template('search.html',user_id=session["user_id"],artistslist=artistslist, artist_info=artist_info)


@app.route('/search/<selectedartistname>', methods = ['GET'])
@login_required
def searchuser(selectedartistname):
    # __tablename__ = 'users'
	# id = db.Column(Integer, primary_key=True) これを含んだURLが飛ばせればよい。

    print(selectedartistname)
    userlist = set([])
    trackdata = db.session.query(songs.track_id).filter(songs.artist_name == selectedartistname).all()
    # userdata = db.session.query(songs.artist_name).filter(songs.artist_name == selectedartistname).all()
    # userdata = db.session.query(songsn)

    for track in trackdata:
        userdata = db.session.query(song_locations.user_id).filter(song_locations.track_id == track[0]).all()
        for id in userdata:
            userlist.add(id[0])
    
    user_info = []
    # for user in userlist:
    #     user_info.append(db.session.query(users.id, users.username).filter(users.id == int(user[0])).first())
    print(userlist)     
    return render_template('search.html',userlist=userlist, user_info=user_info)


# Spotifyの認証ページへリダイレクト
@app.route('/spotify-login')
@login_required
def spotify_login():
    # def create_spotify_oauth()の情報を使いAPIでSpotifyオリジナルの認証ページを取得
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    # 取得したオリジナルページにリダイレクト
    return redirect(auth_url)

# Spotifyオリジナルの認証ページからの帰ってくる場所（SpotifyAPIの設定でこのLocalHost（127.0.0.1）で登録しているため、デプロイの際変更必要）
@app.route('/spotify-authorize')
@login_required
def spotify_authorize():
    sp_oauth = create_spotify_oauth()
    # session.clear()
    # 認証情報をsessionに保存
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    # 仮のページにリダイレクト（これが地図画面になる？）
    return redirect("/")

# Spotifyからログアウト（現在使っていない。もしspotifyだけログアウトしたいならtokeninfoだけsession消す必要あり。）
@app.route('/spotify-logout')
@login_required
def spotify_logout():
    session.clear() 
    return redirect('/')

@app.route('/spotify-loading')
@login_required
def spotify_loading():
    return render_template("loading.html")

# Spotfy認証後のリダイレクトページ
@app.route('/getTrack', methods = ['POST'])
@login_required
def getTrack():
    #認証しているか確認
        session['token_info'], authorized = get_token()
        session.modified = True
        # していなかったらリダイレクト。
        if not authorized:
            return redirect('/spotify-login')    
        sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
        try:
            # 連続で取得すると、エラーするため少し時間を置く（今は問題なさそうだからコメントアウト）
            # time.sleep(3) 
            current_track_info = get_current_track()
            
            # POSTの受け取り
            lat = request.form.get('lat')
            lng = request.form.get('lng')
            emotion = request.form.get('emotion')
            comment = request.form.get('comment')
            # addingで日付受け取った場合
            if request.form.get('date'): 
                date_str = request.form.get('date')
                Datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                date = Datetime.date()
            # loadingで現在地追加の日付を使う場合
            else:
                date = datetime.date.today()
                # Datetime = datetime.datetime.now()
            # get_current_track()で取得したIDを以前取得したものと比較して異なっていたら新しい曲とみなし書き込む。
            if current_track_info['id'] != session.get('current_id'):
                exist_song = db.session.query(songs).filter(songs.track_id == current_track_info["id"]).all()
                if exist_song == []:
                    print(current_track_info["artists"])
                    new_song = songs(track_id=current_track_info["id"], track_name=current_track_info["track_name"], artist_name=current_track_info["artists"], track_image=current_track_info["image"], spotify_url=current_track_info["link"])
                    db.session.add(new_song)
                    db.session.commit()

                new_song_location = song_locations(user_id=session["user_id"], track_id=current_track_info["id"], longitude=lng, latitude=lat, date=date, emotion=emotion, comment=comment)
                db.session.add(new_song_location)
                db.session.commit()     
            session['current_id'] = current_track_info['id']
            return redirect(url_for('profile', display_user_id=session['user_id']))

        except TypeError as e:
            print(
                # エラーの場合原因返す
                e
            )
            return redirect("/")

# 現在再生されている曲情報を取得
def get_current_track():
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    id = sp.current_playback()['item']['id']
    track_name = sp.current_playback()['item']['name']
    artists = [artist for artist in sp.current_playback()['item']['artists']]
    # artist_names = sp.current_playback()['item']['artists']['name']
    # link = sp.current_playback()['item']['album']['external_urls'] #こっちだとアルバムのURL
    link = sp.current_playback()['item']['external_urls']['spotify'] #こっちは曲単体のURL
    image = sp.current_playback()['item']['album']['images'][2]['url']
    # artistが複数ある場合に結合して一つの文字列にする
    artist_names = ', '.join([artist['name'] for artist in artists])
    
    current_track_info = {
        "id": id,
        "track_name": track_name,
        "artists": artist_names,
        "link": link,
        "image": image
    }
    return current_track_info

# Spotify認証の保持の確認
# Checks to see if token is valid and gets a new token if not
def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Checking if token has expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if it has expired
    if (is_token_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid

# SpotifyAPIを使うための情報
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=url_for('spotify_authorize', _external=True),
        scope="user-library-read, playlist-modify-public, playlist-modify-private, user-library-modify, playlist-read-private, user-library-read, user-read-recently-played, user-read-playback-state")

@app.route('/current_location', methods=['GET'])
@login_required
def current_location():
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY
    songdata=[]
    pins = db.session.query(song_locations).filter(song_locations.user_id == session["user_id"]).all()
    
    for pin in pins:
        song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})
        print(pin.date)
    return render_template('current_location.html', user_id=session["user_id"], GOOGLEMAPURL=googlemapURL ,Songdatas=songdata)



@app.route('/map/<song_location_id>/edit', methods=['GET','POST'])
def edit_map(song_location_id):
    songdata = []
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY
    song_location = db.session.query(song_locations).filter(song_locations.id == song_location_id).first()
    # song_locationがないか、他のユーザーのsong_locationの場合
    if not song_location or  song_location.user_id != session["user_id"]:
        return redirect('/')
    song = db.session.query(songs).filter(songs.track_id == song_location.track_id).first()
    songdata.append({'id':song_location.id,'user_id':song_location.user_id, 'lat':song_location.latitude, 'lng':song_location.longitude, 'date':song_location.date.strftime("%Y-%m-%d"),'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'emotion':song_location.emotion, 'comment':song_location.comment})
    if request.method == "POST":
        if request.form.get('date'): 
            date_str = request.form.get('date')
            Datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            date = Datetime.date()
            print(date)
            print("is registerd")
            # loadingで現在地追加の日付を使う場合
        else:
            date = datetime.date.today()
            # Datetime = datetime.datetime.now()
            print(date)
            print("is today")
        song_location.date = date
        song_location.emotion = request.form.get('emotion')
        song_location.comment = request.form.get('comment')
        db.session.commit()
        return redirect('/')
    else:
        return render_template('edit_map.html', GOOGLEMAPURL=googlemapURL, Songdatas=songdata, user_id=session["user_id"], lat=song_location.latitude, lng=song_location.longitude)

@app.route('/map/<song_location_id>/delete', methods=['GET'])
def deletePin(song_location_id):
    song_location = db.session.query(song_locations).filter(song_locations.id == song_location_id).first()
    # song_locationがないか、他のユーザーのsong_locationの場合
    if not song_location or song_location.user_id != session["user_id"]:
        return redirect('/')
    db.session.delete(song_location)
    db.session.commit()
    print("delete pin")
    return redirect(url_for('profile', display_user_id=session['user_id']))

@app.route('/profile/<display_user_id>/period/<displayfrom>/<displayto>', methods = ['GET','POST'])
def profilePeriod(display_user_id,displayfrom, displayto):
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')    
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    # ユーザの情報
    user_id = session["user_id"]
    following_status = ""
    login_user_id = session["user_id"]

    # 表示しているユーザーのフォロー情報
    display_user_id = int(display_user_id) # int型に統一
    if display_user_id == login_user_id:
        following_status = "myself"
    else:
        following = db.session.query(follow).filter(follow.follow_user_id == login_user_id, follow.followed_user_id == display_user_id).first()
        if following:
            following_status = "True"
        else:
            following_status = "False"
    
    # print("following: ", end="")
    # print(following)

    # フォローフォロワー数
    follow_user = db.session.query(follow).filter(follow.follow_user_id == display_user_id).all()
    if follow_user:
        follow_number = len(follow_user)
    else: 
        follow_number = 0

    followed_user = db.session.query(follow).filter(follow.followed_user_id == display_user_id).all()
    if followed_user:
        followed_number = len(followed_user)
    else:
        followed_number = 0
    nickname = db.session.query(users.nickname).filter(users.id == display_user_id).first()
    username = db.session.query(users.username).filter(users.id == display_user_id).first()
    user_info = dict(id=display_user_id, username=username[0], following=following_status, follow_number=follow_number, followed_number=followed_number, nickname=nickname[0])
    print(user_info)
    print(nickname)

    pins = []
    songdata = []
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY

    pins = db.session.query(song_locations).filter(song_locations.user_id == display_user_id).filter(song_locations.date >= displayfrom).filter(song_locations.date <= displayto).all()
    
    for pin in pins:
        # print(pin)
        song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})
    
    if request.method == "GET":
        # playlistlink = db.session.query(made_playlists.playlist_uri).filter(made_playlists.user_id == user_id).all()
        # playlistimage = db.session.query(made_playlists.playlist_image).filter(made_playlists.user_id == user_id).all()

        # print("playlink",playlistlink)
        # print("image",playlistimage)
        return render_template('profile.html',user_id=session["user_id"] ,user_info=user_info, GOOGLEMAPURL=googlemapURL ,Songdatas=songdata, nowdisplayfrom=displayfrom, nowdisplayto=displayto, display_user_id=display_user_id )
    
    if request.method == "POST":
        #makeplaylistにデータ渡す
        playlist_name = request.form['playlistname']
        return render_template('makeplaylist.html', data = songdata, name = playlist_name)


@app.route('/confirm', methods=['GET','POST'])
def confirm():
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))

    if request.method == 'POST':

        url_list = request.form.getlist('urls')
        # flash("以下の曲が条件に当てはまりました", "success")
        playlist_name = request.form.get("playlist_name")
        sp_user_id = sp.current_user()['id']
        
        new_playlist = sp.user_playlist_create(sp_user_id, playlist_name)
        sp.user_playlist_add_tracks(sp_user_id, new_playlist["id"], url_list)

        #プレイリストIDをsessionに保存
        playlist_id = sp.current_user_playlists()['items'][0]['id']
        #プレイリストURIをsessionに保存
        playlist_uri_test = sp.current_user_playlists()['items'][0]['uri']
        playlist_uri = playlist_uri_test.removeprefix('spotify:playlist:')
        session['playlist_uri'] = playlist_uri

        #曲を追加
        # periodsongs = db.session.query(song_locations.track_id).filter(song_locations.user_id == user_id).filter(song_locations.date >= displayfrom).filter(song_locations.date <= displayto).all()
        # print("this",periodsongs)

        # numbers = len(periodsongs)
        # [sp.playlist_add_items(playlist_id = playlist_id, items = [periodsongs[i][0]], position=None) for i in range(0, numbers)]
        
        playlist_image = sp.playlist_cover_image(playlist_id)[0]['url']


        new_playlist = made_playlists(user_id=session["user_id"],playlist_id = playlist_id ,playlist_uri=playlist_uri,playlist_image=playlist_image)
        db.session.add(new_playlist)
        db.session.commit()    
        
        playlistaa = db.session.query(made_playlists.playlist_uri).filter(made_playlists.user_id == session["user_id"]).all()
        print("play",playlistaa[0] )

        return redirect('/playlist')


@app.route('/playlist', methods = ['GET'])
def playlist():
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')    
    
    playlist_date = db.session.query(made_playlists).filter(made_playlists.user_id == session["user_id"]).all()
    playlists =[]

    for pin in playlist_date:
        print(pin.playlist_id)
        playlists.append({'id':pin.id,'user_id':pin.user_id, 'playlist_id':pin.playlist_id, 'playlist_uri':pin.playlist_uri,
        'playlist_image':pin.playlist_image})

    return render_template('playlist.html', playlists = playlists,user_id = session['user_id']) 


@app.route('/home/period/<displayfrom>/<displayto>', methods = ['GET'])
def homePeriod(displayfrom, displayto):
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')    
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    # ユーザの情報
    user_id = session["user_id"]
    user_info = []
    track_id = db.session.query(song_locations.track_id).filter(song_locations.user_id == user_id).all()
    nickname = db.session.query(users.nickname).filter(users.id == user_id).first()
    user_info.append(track_id)
    user_info.append(nickname[0])
    print(user_id)
    print(user_info)
    print(nickname)

    pins = []
    songdata = []
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY

    pins = db.session.query(song_locations).filter(song_locations.date >= displayfrom).filter(song_locations.date <= displayto).all()
    
    for pin in pins:
        # print(pin)
        song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})

    return render_template('index.html',user_id=session["user_id"] ,user_info=user_info, GOOGLEMAPURL=googlemapURL ,Songdatas=songdata, nowdisplayfrom=displayfrom, nowdisplayto=displayto)


@app.route('/select_location', methods = ['GET'])
@login_required
def select_location():
    session['token_info'], authorized = get_token()
    session.modified = True
    # していなかったらリダイレクト。
    if not authorized:
        return redirect('/spotify-login')
    songdata = []
    pins = db.session.query(song_locations).filter(song_locations.user_id == session["user_id"]).all()
    for pin in pins:
        song = db.session.query(songs).filter(songs.track_id == pin.track_id).first()
        songdata.append({'id':pin.id,'lat':pin.latitude, 'lng':pin.longitude, 'date':pin.date.strftime("%Y-%m-%d"),
        'artist':song.artist_name, 'track':song.track_name, 'image':song.track_image ,'link':song.spotify_url, 'user_id':pin.user_id, 'emotion':pin.emotion, 'comment':pin.comment})
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    googlemapURL = "https://maps.googleapis.com/maps/api/js?key="+GOOGLE_MAP_API_KEY   
    return render_template('select_location.html', GOOGLEMAPURL=googlemapURL, Songdatas = songdata, user_id = session["user_id"])


# if __name__ == '__main__':
#     app.run(host=os.getenv('APP_ADDRESS', 'localhost'), port=5000)
    
    
# if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    # app.run(host=os.getenv('APP_ADDRESS', 'localhost'), port=5000)
    # app()
    # The app is not in debug mode or we are in the reloaded process

# if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#     app.run(host=os.getenv('APP_ADDRESS', 'localhost'), port=5000)

    # app.run_server(use_reloader=False)

if __name__ == '__main__':
    # app.run(host=os.getenv('APP_ADDRESS', 'localhost'), port=5000)
    app()