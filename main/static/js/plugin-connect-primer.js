/************************************************************************************
 /*
 /*      Copyright Â© 2024 SlicPix Inc. USA. All rights reserved.
 /*
 /************************************************************************************/
 ;(function ( ns, undefined ) {

	/*---------- fetch_css -------------*/
    var fetch_css=function(target,cb){
	    var head  = document.getElementsByTagName('head')[0];
	    var link  = document.createElement('link');
	    link.rel  = 'stylesheet';
	    link.type = 'text/css';
	    link.href = spix._resources_ep + target;
	    if (cb) { link.onload = function() { cb() }; }
	    head.appendChild(link);
	};	/* end fetch_css */
	ns.fetch_css=fetch_css;

	/*---------- fetch_library -------------*/
	var fetch_library=function(target,attributes,cb){
	  	var script = document.createElement( "script" );
	  	script.type = "text/javascript";
	  	if(script.readyState){
		    script.onreadystatechange = function(){
		      	if ( script.readyState === "loaded" || script.readyState === "complete" )
		        	script.onreadystatechange = null;
		    };
	  	}else{  
	    	script.onload = function() { cb(target); };
	  	}
	  	script.src = spix._resources_ep + target;
	  	if (attributes != null){
	  		for(const property in attributes){
	  			script.setAttribute(property,attributes[property]);
	  		}
	  	}
	  	document.getElementsByTagName( "head" )[0].appendChild( script );
	}; /* end fetch_library */
	ns.fetch_library=fetch_library

	function r(f){
        if (document.readyState === 'interactive' || document.readyState === 'complete'){
            clearTimeout(bootstrap_timeout_cancel);
            f();
        }else
            bootstrap_timeout_cancel=setTimeout('spix.bootstrap('+f+')',15);
    }
    ns.bootstrap=r;

    /*---------- bootstrap -------------*/
    (function () {
      	spix.bootstrap(function(){
      		var results;
      		var fetched=0;

      		var cb=function(){
	     		fetched++;
	      		if (fetched == results.length){
	      			var query='[data-is-image="true"]';
					var plugin=document.querySelector(query);
					var account = plugin.getAttribute("data-is-account");
					if (account != null && account.trim().length > 0)
						spix.connect(account);
	      		}
	      	}

	      	var script=document.querySelector('[data-is-id="is-plugin-connect-primer"]');
	      	if (script != null){
	      		var src = script.getAttribute("src");
	      		if (src.includes("interactivity04342.slicpixdev.com"))
	      			spix._resources_ep = "https://interactivity04342.slicpixdev.com/";
	      		else
	      			spix._resources_ep = "https://interactivity.studio/";
		      	fetch(spix._resources_ep + "plugin/resources").then(
					function(response){
						if (response.ok)
							return response.json();
						else
							return Promise.reject(response);
					}).then(
						function(r){
							results=r.resources;
							var entry;
							for (var i = 0;i<results.length;i++){
								entry=results[i];
								switch(entry.type){
									case "javascript":
										spix.fetch_library(entry.ep,null,cb);
										break;
									case "stylesheet":
										spix.fetch_css(entry.ep,cb);
										break;
								}
							}
						}
					).catch(
					function(err){
						//fall silent
					}
				);
		    }       
	   	});
    })(); /* end bootsrap  */

})(window.spix = window.spix || {});