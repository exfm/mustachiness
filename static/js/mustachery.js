
//var search_url = 'static/js/standard.json';
// var search_url = 'http://mustachiness.ex.fm/api/data?title=Alive&artist=Pearl%20Jam';

$(function(){


	// get data

	function getStacheData(artist, title, el){
		var search_url = 'http://mustachiness.ex.fm/api/data?title='+title+'&artist='+artist;
		$.ajax({
			url:search_url,
			success:function(data){
				makeStache(data, el);
			}
		})
	}

	// draw a songStache!
	function makeStache(data, el){
		var maxWidth = 900;
		var minWidth = 250;

		if (data.song){
			data = data.song;
		}


		// mustache defaults

		var mHeight = 150;
		var padding = 20;
		var mWidth = maxWidth/2 - padding/2;

		var divot = data.song_hotttnesss * 5;

		var taperStart = .5 * mWidth;
		var taperLength = mWidth - taperStart;
		var direction = data.audio_summary.energy >= .5 ? 1 : -1;

		var curl = data.audio_summary.danceability * .001 * direction;
		var fatness = Math.abs(data.audio_summary.loudness);

		//console.log(curl, fatness)

		// canvas goodness
		var canvas = document.createElement('canvas');
		var ctx = canvas.getContext('2d');

		var duration = data.audio_summary.duration;

		$(canvas).attr('width', maxWidth);
		$(canvas).attr('height', mHeight*2 + padding*2);


		lData = data.loudness;
		var size = _.size(lData);

		var step = Math.floor(size/((maxWidth-padding)/2));



		var allTimestamps = _.keys(lData).sort();
		var timestamps = [];
		_.each(allTimestamps, function(t, i){
			if( !(i % step) && i != 0){
				timestamps.push([t, lData[t]]);
			}
		});

		// cached element
		var cacheStache = document.createElement('canvas');
	    cacheStache.width = mWidth + padding;
	    cacheStache.height = mHeight*2 + padding;
	    cachectx = cacheStache.getContext('2d');


		var x1 = 0,
			y1 = 0,
			x2 = 0,
			y2 = 0;

		var r = Math.floor(107 * data.audio_summary.energy),
			g = Math.floor(60 * data.audio_summary.energy),
			b = Math.floor(31 * data.audio_summary.energy);

		var prevLoudness = 0;

		for(var i = 0; i < mWidth; i++){
			try{
				var l = Math.abs(timestamps[i][1]);
			} catch(e){
				var l = Math.abs(timestamps[i]);
			}
			var h = l + fatness;

			if(i > taperStart){
				var percentLeft = (taperLength - (i - taperStart))/taperLength;
				h = h * percentLeft;
			}

			var vStrip = document.createElement('canvas');
			vStrip.width = 2;
			var vh = Math.floor(h);

	    	vStrip.height = Math.floor(h*2) || 1;
	    	var v_ctx = vStrip.getContext('2d');

			v_ctx.fillStyle = 'rgb('+r+','+g+','+b+')';

			var lDelta = fatness - l;
			var curlTarget = lDelta * .0001;

			curl += (curlTarget - prevLoudness)/2;

			prevLoudness = curlTarget;


			cachectx.rotate(i*curl * (Math.PI/180));
			v_ctx.fillRect(0,0,2,h*2);


			//cachectx.fillRect(i,mHeight-h,1,h*2);
			cachectx.drawImage(vStrip, i, mHeight-h);

		}

		// RIGHT
		var stacheRight = document.createElement('canvas');
		stacheRight.width = mWidth + padding;
		stacheRight.height = mHeight*2 + padding;
		sr_ctx = stacheRight.getContext('2d');

		sr_ctx.drawImage(cacheStache, divot, 0);

		ctx.drawImage(stacheRight, mWidth + padding, padding);

		// LEFT
		var stacheLeft = document.createElement('canvas');
		stacheLeft.width = mWidth + padding;
		stacheLeft.height = mHeight*2 + padding;
		sl_ctx = stacheLeft.getContext('2d');
		sl_ctx.scale(-1,1);
		sl_ctx.translate(-mWidth, 0);
		sl_ctx.drawImage(stacheRight, 0, 0);
		ctx.drawImage(stacheLeft, padding, padding);

		var div = '#'+el;
		$(div).append(canvas);

		var imgData = canvas.toDataURL("image/png");
		$.post(
			'/upload-stache',
			{'stache': imgData, 'song_id': data.id},
			function(resp){
				console.log(resp);
			}
		);
	}

	window.makeStache = makeStache;
	window.getStacheData = getStacheData;
})

