
var search_url = 'static/js/standard.json';
var search_url = 'http://mustachiness.ex.fm/api/data?title=%22Run%22&artist=%22Snow%20Patrol%22';

$(function(){


	// get data
	$.ajax({
			url:search_url,
			success:function(data){
				makeStache(data, 'testdiv');
			}
		}
	)

	// draw a songStache!
	function makeStache(data, el){

		// mustache defaults
		var mWidth = 200;
		var mHeight = 60;
		var divot = 5;
		var taperStart = .5 * mWidth;
		var taperLength = mWidth - taperStart;
		var curl;

		// canvas goodness
		var canvas = document.createElement('canvas');
		var ctx = canvas.getContext('2d');

		$(canvas).attr('width', mWidth*2 + divot);
		$(canvas).attr('height', mHeight*2);

		if(data.song){
			data = data.song;
		}
		var duration = data.audio_summary.duration;

		lData = data.loudness;
		var size = _.size(lData);

		var step = Math.floor(size/mWidth);
		var allTimestamps = _.keys(lData).sort();
		var timestamps = [];
		_.each(allTimestamps, function(t, i){
			if( !(i % step) && i != 0){
				timestamps.push([t, lData[t]]);
			}
		});

		// cached element
		var cacheStache = document.createElement('canvas');
	    cacheStache.width = mWidth;
	    cacheStache.height = mHeight*2;
	    cachectx = cacheStache.getContext('2d');



		for(var i = 0; i < mWidth; i++){
			var h = Math.abs(timestamps[i][1]);

			if(i > taperStart){
				var percentLeft = (taperLength - (i - taperStart))/taperLength;
				h = h * percentLeft;
			}

			var vStrip = document.createElement('canvas');
			vStrip.width = 2;
			var vh = Math.floor(h);

	    	vStrip.height = Math.floor(h*2) || 1;
	    	var v_ctx = vStrip.getContext('2d');


			//cachectx.save();
			cachectx.rotate(-i*.0005 * (Math.PI/180));
			//cachectx.rotate(i*.01)
			v_ctx.fillRect(0,0,2,h*2);


			//cachectx.fillRect(i,mHeight-h,1,h*2);
			cachectx.drawImage(vStrip, i, mHeight-h);
			//cachectx.restore();
		}

		// RIGHT
		var stacheRight = document.createElement('canvas');
		stacheRight.width = mWidth;
		stacheRight.height = mHeight*2;
		sr_ctx = stacheRight.getContext('2d');

		sr_ctx.drawImage(cacheStache, divot, 0);

		ctx.drawImage(stacheRight, mWidth, 0);

		// LEFT
		var stacheLeft = document.createElement('canvas');
		stacheLeft.width = mWidth;
		stacheLeft.height = mHeight*2;
		sl_ctx = stacheLeft.getContext('2d');
		sl_ctx.scale(-1,1);
		sl_ctx.translate(-mWidth, 0);
		sl_ctx.drawImage(stacheRight, 0, 0);
		ctx.drawImage(stacheLeft, 0, 0);

		var div = '#'+el;
		$(div).append(canvas);
	}
	window.makeStache = makeStache;
})

