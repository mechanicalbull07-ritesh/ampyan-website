(function(){
  "use strict";
  document.querySelectorAll("[data-busy-form]").forEach(function(form){
    form.addEventListener("submit",function(){
      var button=form.querySelector('button[type="submit"]');
      if(button){button.disabled=true;button.setAttribute("aria-busy","true");}
    });
  });
  document.querySelectorAll("[data-copy-url]").forEach(function(button){
    button.addEventListener("click",async function(){
      try{await navigator.clipboard.writeText(button.dataset.copyUrl);button.textContent="Copied";}
      catch(error){button.textContent="Copy unavailable";}
    });
  });
  var editor=document.querySelector("[data-blog-editor]");
  if(editor){
    var source=editor.querySelector("[data-block-json]"),list=editor.querySelector("[data-block-list]"),blocks=[];
    try{blocks=JSON.parse(source.value||"[]");if(!Array.isArray(blocks))blocks=[];}catch(error){blocks=[];}
    var dirty=false;
    function blockId(){return(window.crypto&&crypto.randomUUID)?crypto.randomUUID():"block-"+Date.now()+"-"+Math.random().toString(36).slice(2);}
    function sync(){blocks.forEach(function(block,index){block.id=String(block.id||blockId());block.order=index;block.data=(block.data&&typeof block.data==="object")?block.data:{};});source.value=JSON.stringify(blocks);}
    function field(label,value,handler){var wrap=document.createElement("label"),input=document.createElement("textarea");wrap.textContent=label;input.rows=3;input.value=value||"";input.addEventListener("input",function(){handler(input.value);sync();dirty=true;});wrap.appendChild(input);return wrap;}
    function renderEditor(){sync();list.textContent="";blocks.forEach(function(block,index){var card=document.createElement("section");card.className="blog-block-card";var heading=document.createElement("h3");heading.textContent=(index+1)+". "+String(block.type).replaceAll("_"," ");card.appendChild(heading);
      if(["paragraph","heading","quote","callout"].includes(block.type))card.appendChild(field("Text",block.data.text,function(value){block.data.text=value;}));
      if(["image","youtube","instagram","link_preview"].includes(block.type))card.appendChild(field("HTTPS URL",block.data.url,function(value){block.data.url=value;}));
      if(["bullet_list","numbered_list"].includes(block.type))card.appendChild(field("Items (one per line)",(block.data.items||[]).map(function(item){return typeof item==="object"?item.text:item;}).join("\n"),function(value){block.data.items=value.split("\n").filter(Boolean);}));
      if(block.type==="gallery")card.appendChild(field("Image HTTPS URLs (one per line)",(block.data.items||block.data.images||[]).map(function(item){return item.url||"";}).join("\n"),function(value){block.data.items=value.split("\n").filter(Boolean).map(function(url){return{url:url,caption:"Gallery image"};});delete block.data.images;}));
      if(block.type==="table")card.appendChild(field("CSV rows (first row is header)",[block.data.headers||[]].concat(block.data.rows||[]).map(function(row){return row.join(",");}).join("\n"),function(value){var rows=value.split("\n").filter(Boolean).map(function(row){return row.split(",").map(function(cell){return cell.trim();});});block.data.headers=rows.shift()||[];block.data.rows=rows;}));
      var controls=document.createElement("div");controls.className="ui-button-row";[["Move up",-1],["Move down",1]].forEach(function(action){var button=document.createElement("button");button.type="button";button.textContent=action[0];button.disabled=(index===0&&action[1]<0)||(index===blocks.length-1&&action[1]>0);button.addEventListener("click",function(){blocks.splice(index+action[1],0,blocks.splice(index,1)[0]);dirty=true;renderEditor();});controls.appendChild(button);});var remove=document.createElement("button");remove.type="button";remove.textContent="Remove block";remove.addEventListener("click",function(){blocks.splice(index,1);dirty=true;renderEditor();});controls.appendChild(remove);card.appendChild(controls);list.appendChild(card);});}
    editor.querySelector("[data-add-block]").addEventListener("click",function(){blocks.push({id:blockId(),type:editor.querySelector("[data-new-block-type]").value,order:blocks.length,data:{}});dirty=true;renderEditor();});
    editor.addEventListener("input",function(){dirty=true;});
    editor.addEventListener("submit",function(){sync();dirty=false;});
    window.addEventListener("beforeunload",function(event){
      if(dirty){event.preventDefault();event.returnValue="";}
    });
    var previewButton=editor.querySelector("[data-preview-blocks]");
    if(previewButton) previewButton.addEventListener("click",function(){
      var output=document.querySelector("[data-blog-preview]");
      output.textContent="";
      try{
        blocks.forEach(function(block){
          var node=document.createElement(block.type==="heading"?"h3":"p");
          node.textContent=(block.data&&block.data.text)||("["+String(block.type||"block")+"]");
          output.appendChild(node);
        });
      }catch(error){output.textContent="Content blocks JSON is invalid.";}
    });
    editor.querySelector("[data-upload-media]").addEventListener("click",async function(){var input=editor.querySelector("[data-media-file]"),status=editor.querySelector("[data-media-status]"),file=input.files[0];if(!file){status.textContent="Choose an image first.";return;}var token=editor.querySelector('[name="csrf_token"]').value,body=new FormData();body.append("image",file);body.append("csrf_token",token);try{status.textContent="Uploading…";var response=await fetch("/blogs/media",{method:"POST",body:body,credentials:"same-origin",headers:{"X-CSRFToken":token}});var result=await response.json();if(!response.ok||!result.success)throw new Error(result.message||"Upload failed.");blocks.push({id:blockId(),type:"image",order:blocks.length,data:{url:result.media.url,alt_text:file.name}});dirty=true;renderEditor();status.textContent="Image added.";}catch(error){status.textContent=error.message||"Image upload failed.";}});
    renderEditor();
  }
})();
