//  表示期間切り替え 
function period(){
  var url = "/home/period/";
  let from = document.getElementById('from').value;
  let newfrom = from.replace(/\//g,"-");

  let to = document.getElementById('to').value;
  let newtill = to.replace(/\//g,"-");
  if( document.getElementById('from').value ){
    url += newfrom;
  }
  if( document.getElementById('to').value ){
    url += '/' + newtill;
  }
  location.href = url;
}

// 地図関連
let map;
let mainMarker;
let marker =[];
let infoWindow = [];

function initMap() {
  var map = new google.maps.Map(document.getElementById('map'), {
      zoom: 14,
      center: {lat: 35.665498, lng: 139.75964}
  });

  
  console.log(SongData);

  // 複数ピンを立てる
  for (var i = 0; i < SongData.length; i++) {
  
    // マーカーの追加
    marker[i] = new google.maps.Marker({
      position: new google.maps.LatLng( SongData[i]['lat'], SongData[i]['lng']),
      map: map,
      icon: SongData[i]['image'],
    });

    // 吹き出し作成
    var box_node = document.createElement('div');
    var p_node_date = document.createElement('p');
    var text_node_date = document.createTextNode(SongData[i]["date"]);
    p_node_date.appendChild(text_node_date);
    box_node.appendChild(p_node_date);

    var p_node_artist = document.createElement('p');
    var text_node_artist = document.createTextNode("Artist：" + SongData[i]["artist"]);
    p_node_artist.appendChild(text_node_artist);
    box_node.appendChild(p_node_artist);

    var p_node_track = document.createElement('p');
    var text_node_track = document.createTextNode("曲名：" + SongData[i]["track"]);
    p_node_track.appendChild(text_node_track);
    box_node.appendChild(p_node_track);

    var p_node_emotion = document.createElement('p');
    var text_node_emotion = document.createTextNode("感情：" + SongData[i]["emotion"]);
    p_node_emotion.appendChild(text_node_emotion);
    box_node.appendChild(p_node_emotion);

    var p_node_comment = document.createElement('p');
    var text_node_comment = document.createTextNode("コメント：" + SongData[i]["comment"]);
    p_node_comment.appendChild(text_node_comment);
    box_node.appendChild(p_node_comment);

    var p_node_spotify = document.createElement("p");
    var a_node_spotify = document.createElement("a");
    a_node_spotify.href = SongData[i]["link"];
    var text_node_spotify = document.createTextNode("Open Spotify");
    a_node_spotify.appendChild(text_node_spotify);
    p_node_spotify.appendChild(a_node_spotify);
    box_node.appendChild(p_node_spotify);

    // 自分の作ったピンしか編集ボタンを表示しない
    console.log(UserId)
    if (UserId == SongData[i]["user_id"]){
      console.log(SongData[i]["id"] )
      var a_node_edit = document.createElement("a");
      a_node_edit.href = "/map/" + SongData[i]["id"] + "/edit";
      var text_node_edit = document.createTextNode("編集");
      a_node_edit.appendChild(text_node_edit);
      box_node.appendChild(a_node_edit);
    }

    // 吹き出しの追加
    infoWindow[i] = new google.maps.InfoWindow({
    // 吹き出しに詳細を追加（ほんとはboxをはりつけたい。）
    content: box_node
    });

    markerEvent(i); 
  }

  // マーカークリック時に吹き出しを表示する（複数ピンに対して）
  function markerEvent(i) {
    marker[i].addListener('click', function() {
      infoWindow[i].open(map, marker[i]); //一つの時とmakerの変数が違うから注意
    });
  }
//  複数ピンをたてるここまで。
}