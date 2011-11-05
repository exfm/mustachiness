
var search_url = 'static/js/standard.json';
//var search_url = 'http://mustachiness.ex.fm/api/data?title=%22Run%22&artist=%22Snow%20Patrol%22';

$(function(){


	// get data
	// $.ajax({
	// 		url:search_url,
	// 		success:function(data){
	// 			makeStache(data, 'testdiv');
	// 		}
	// 	}
	// )

	// draw a songStache!
	function makeStache(data, el){
		console.log(data, el)
		// mustache defaults
		var mWidth = 200;
		var mHeight = 60;
		var divot = 5;
		var taperStart = 0.5 * mWidth;
		var taperLength = mWidth - taperStart;

		var curl;

		// canvas goodness
		var canvas = document.createElement('canvas');
		var ctx = canvas.getContext('2d');

		$(canvas).attr('width', mWidth*2 + divot);
		$(canvas).attr('height', mHeight*2);


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
	    cacheStache.height = mHeight;

	    cachectx = cacheStache.getContext('2d');

		for(var i = 0; i < mWidth; i++){
			var h = Math.abs(timestamps[i][1]);

			if(i > taperStart){
				var percentLeft = (taperLength - (i - taperStart))/taperLength;
				console.log(percentLeft, i);
				h = h * percentLeft;
			}

			cachectx.fillRect(i,0,1,h);
		}


		// bottom right
		ctx.drawImage(cacheStache, mWidth + divot, mHeight);


		// top right
		var tr = document.createElement('canvas');
	    tr.width = mWidth;
	    tr.height = mHeight;
		trctx = tr.getContext('2d');
		trctx.scale(1,-1);
		trctx.translate(0,-mHeight);
		trctx.drawImage(cacheStache, 0, 0);
		ctx.drawImage(tr, mWidth + divot, 0);

		// bottom left
		var bl = document.createElement('canvas');
	    bl.width = mWidth;
	    bl.height = mHeight;
		blctx = bl.getContext('2d');
		blctx.scale(-1,1);
		blctx.translate(-mWidth,0);
		blctx.drawImage(cacheStache, 0, 0);
		ctx.drawImage(bl, 0, mHeight);

		// top left
		var tl = document.createElement('canvas');
	    tl.width = mWidth;
	    tl.height = mHeight;
		tlctx = tl.getContext('2d');
		tlctx.scale(-1,-1);
		tlctx.translate(-mWidth,-mHeight);
		tlctx.drawImage(cacheStache, 0, 0);
		ctx.drawImage(tl, 0, 0);

		var div = '#'+el;
		$(div).append(canvas);
		console.log($(div));
	}
	window.makeStache = makeStache;
});

