(function(){
"use strict";
var root=document.querySelector("[data-news-editor]");
if(!root)return;
var blocksHost=root.querySelector("[data-blocks]");
var hidden=root.querySelector('input[name="content_blocks"]');
var initialPayload=root.querySelector("#initialNewsBlocks");
var legacy=root.querySelector('textarea[name="content"]');
var status=root.querySelector("[data-editor-status]");
var preview=root.querySelector("[data-editor-preview]");
var blocks=[];
var allowed=["paragraph","heading","subheading","bullet_list","numbered_list","image","gallery","quote","highlight","key_data","table","divider","youtube","instagram"];

function text(value){return String(value==null?"":value).trim();}
function escapeHtml(value){var node=document.createElement("div");node.textContent=String(value||"");return node.innerHTML;}
function setStatus(message){status.textContent=message||"";}
function initialBlocks(){
  var source=initialPayload?initialPayload.textContent:hidden.value;
  if(!source.trim())return [];
  try{var parsed=JSON.parse(source);return parsed&&Array.isArray(parsed.blocks)?parsed.blocks.filter(function(item){return item&&allowed.indexOf(item.type)>=0;}):[];}catch(error){setStatus("Existing rich content could not be loaded. Legacy content is still safe.");return [];}
}
function blank(type){
  if(type==="paragraph")return {type:type,content:[{text:""}]};
  if(type==="heading")return {type:type,level:2,text:""};
  if(type==="subheading")return {type:type,text:""};
  if(type==="bullet_list"||type==="numbered_list")return {type:type,items:[]};
  if(type==="image")return {type:type,url:"",caption:"",alt_text:""};
  if(type==="gallery")return {type:type,images:[]};
  if(type==="quote")return {type:type,content:[{text:""}],cite:""};
  if(type==="highlight")return {type:type,title:"Important",content:[{text:""}]};
  if(type==="key_data")return {type:type,items:[]};
  if(type==="table")return {type:type,headers:[],rows:[]};
  if(type==="youtube"||type==="instagram")return {type:type,url:""};
  return {type:type};
}
function inlineHtml(runs){return (Array.isArray(runs)?runs:[]).map(function(run){var value=escapeHtml(run.text);if(run.italic)value="<em>"+value+"</em>";if(run.bold)value="<strong>"+value+"</strong>";if(run.link)value='<a href="'+escapeHtml(run.link)+'">'+value+"</a>";return value;}).join("");}
function readInline(element){
  var runs=[];
  function walk(node,style){
    if(node.nodeType===Node.TEXT_NODE){if(node.nodeValue){runs.push({text:node.nodeValue,bold:style.bold||undefined,italic:style.italic||undefined,link:style.link||undefined});}return;}
    if(node.nodeType!==Node.ELEMENT_NODE)return;
    var tag=node.tagName.toLowerCase();var next={bold:style.bold||tag==="strong"||tag==="b",italic:style.italic||tag==="em"||tag==="i",link:style.link};
    if(tag==="a")next.link=node.getAttribute("href")||undefined;
    if(tag==="div"||tag==="p"||tag==="br")runs.push({text:"\n"});
    Array.prototype.forEach.call(node.childNodes,function(child){walk(child,next);});
  }
  Array.prototype.forEach.call(element.childNodes,function(node){walk(node,{});});
  return runs.map(function(run){run.text=run.text||"";Object.keys(run).forEach(function(key){if(run[key]===undefined)delete run[key];});return run;}).filter(function(run){return run.text.length;});
}
function editable(label,value,name){return '<label>'+label+'<div class="news-contenteditable" contenteditable="true" data-field="'+name+'" data-placeholder="Write here…">'+inlineHtml(value)+'</div></label>';}
function field(label,value,name,type,placeholder){var hint=placeholder?' placeholder="'+escapeHtml(placeholder)+'"':'';if(type==="textarea")return '<label>'+label+'<textarea data-field="'+name+'" rows="5"'+hint+'>'+escapeHtml(value)+'</textarea></label>';return '<label>'+label+'<input data-field="'+name+'" type="text" value="'+escapeHtml(value)+'"'+hint+'></label>';}
function lines(items){return (items||[]).map(function(item){return Array.isArray(item)?item.map(function(run){return run.text||"";}).join(""):String(item||"");}).join("\n");}
function editorBody(block){
  if(block.type==="paragraph")return '<div class="news-editor-toolbar"><button type="button" data-format="bold"><b>Bold</b></button><button type="button" data-format="italic"><i>Italic</i></button><button type="button" data-format="link">Link</button></div>'+editable("Paragraph",block.content,"content");
  if(block.type==="heading")return field("Heading",block.text,"text")+'<label>Level<select data-field="level"><option value="2">H2</option><option value="3">H3</option><option value="4">H4</option></select></label>';
  if(block.type==="subheading")return field("Subheading",block.text,"text");
  if(block.type==="bullet_list"||block.type==="numbered_list")return field("One item per line",lines(block.items),"items","textarea");
  if(block.type==="image")return '<button type="button" data-upload="single">Upload image</button>'+field("Image URL",block.url,"url")+field("Caption",block.caption,"caption")+field("Alt text",block.alt_text,"alt_text");
  if(block.type==="gallery")return '<button type="button" data-upload="gallery">Upload multiple images</button><input type="file" data-files hidden multiple accept="image/png,image/jpeg,image/webp">'+field("Images: URL | caption | alt text, one per line",(block.images||[]).map(function(image){return [image.url,image.caption||"",image.alt_text||""].join(" | ");}).join("\n"),"images","textarea");
  if(block.type==="quote")return editable("Quote",block.content,"content")+field("Citation",block.cite,"cite");
  if(block.type==="highlight")return field("Label",block.title,"title")+editable("Highlighted text",block.content,"content");
  if(block.type==="key_data")return field("One card per line: Label | Value",(block.items||[]).map(function(item){return item.label+" | "+item.value;}).join("\n"),"items","textarea");
  if(block.type==="table")return field("Header cells separated by |",(block.headers||[]).join(" | "),"headers")+field("Rows: cells separated by |, one row per line",(block.rows||[]).map(function(row){return row.join(" | ");}).join("\n"),"rows","textarea");
  if(block.type==="youtube")return field("YouTube video URL",block.url,"url",null,"Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ");
  if(block.type==="instagram")return field("Instagram post or reel URL",block.url,"url",null,"Example: https://www.instagram.com/reel/ABC_123/");
  return '<p>This divider adds visual separation.</p>';
}
function render(){
  blocksHost.innerHTML="";
  if(!blocks.length){blocksHost.innerHTML='<div class="news-editor-empty">No rich blocks yet. Paste legacy content and select “Convert pasted text,” or add a block.</div>';sync();return;}
  blocks.forEach(function(block,index){
    var card=document.createElement("section");card.className="news-block-editor";card.dataset.index=index;
    card.innerHTML='<div class="news-block-editor-header"><strong>'+escapeHtml(block.type.replaceAll("_"," "))+'</strong><div class="news-block-actions"><button type="button" data-move="up" aria-label="Move up">↑</button><button type="button" data-move="down" aria-label="Move down">↓</button><button type="button" data-remove>Remove</button></div></div>'+editorBody(block);
    if(block.type==="heading")card.querySelector('[data-field="level"]').value=String(block.level||2);
    blocksHost.appendChild(card);
  });sync();
}
function parsePipe(line){return line.split("|").map(function(cell){return text(cell);});}
function capture(){
  Array.prototype.forEach.call(blocksHost.querySelectorAll(".news-block-editor"),function(card){
    var block=blocks[Number(card.dataset.index)];
    Array.prototype.forEach.call(card.querySelectorAll("[data-field]"),function(input){
      var name=input.dataset.field;
      if(input.classList.contains("news-contenteditable")){block[name]=readInline(input);return;}
      var value=input.value;
      if(name==="level"){block.level=Number(value);return;}
      if(name==="items"&&["bullet_list","numbered_list"].indexOf(block.type)>=0){block.items=value.split(/\r?\n/).map(text).filter(Boolean).map(function(item){return [{text:item}];});return;}
      if(name==="items"&&block.type==="key_data"){block.items=value.split(/\r?\n/).map(parsePipe).filter(function(row){return row.some(Boolean);}).map(function(row){return {label:row[0]||"",value:row.slice(1).join(" | ")};});return;}
      if(name==="images"){block.images=value.split(/\r?\n/).map(parsePipe).filter(function(row){return row[0];}).map(function(row){return {url:row[0],caption:row[1]||"",alt_text:row[2]||""};});return;}
      if(name==="headers"){block.headers=parsePipe(value).filter(Boolean);return;}
      if(name==="rows"){block.rows=value.split(/\r?\n/).map(parsePipe).filter(function(row){return row.some(Boolean);});return;}
      block[name]=value;
    });
  });sync();
}
function sync(){hidden.value=blocks.length?JSON.stringify({version:1,blocks:blocks}):"";}
function convertPaste(){
  var value=legacy.value.replace(/\r/g,"").trim();if(!value){setStatus("Paste or write legacy content first.");return;}
  var groups=value.split(/\n\s*\n/);var converted=[];
  groups.forEach(function(group){var rows=group.split("\n").map(text).filter(Boolean);if(!rows.length)return;
    if(rows.every(function(row){return /^[-*•]\s+/.test(row);})){converted.push({type:"bullet_list",items:rows.map(function(row){return [{text:row.replace(/^[-*•]\s+/,"")}];})});}
    else if(rows.every(function(row){return /^\d+[.)]\s+/.test(row);})){converted.push({type:"numbered_list",items:rows.map(function(row){return [{text:row.replace(/^\d+[.)]\s+/,"")}];})});}
    else{converted.push({type:"paragraph",content:[{text:rows.join("\n")} ]});}
  });blocks=converted;render();setStatus("Pasted text converted. Review headings, emphasis and media before publishing.");
}
async function uploadFiles(files,block,gallery){
  if(!files.length)return;setStatus("Uploading article image…");var uploaded=[];
  for(var i=0;i<files.length;i++){var body=new FormData();body.append("image",files[i]);var response=await fetch(root.dataset.uploadUrl,{method:"POST",body:body,credentials:"same-origin"});var data=await response.json().catch(function(){return {};});if(!response.ok||!data.success){setStatus(data.message||"Image upload failed safely.");return;}uploaded.push({url:data.url,caption:"",alt_text:""});}
  if(gallery){block.images=(block.images||[]).concat(uploaded);}else{block.url=uploaded[0].url;}render();setStatus(uploaded.length+" image"+(uploaded.length===1?"":"s")+" uploaded.");
}
function appendInline(parent,runs){(Array.isArray(runs)?runs:[]).forEach(function(run){var leaf=document.createTextNode(run.text||"");var node=leaf;
  if(run.italic){var em=document.createElement("em");em.appendChild(node);node=em;}
  if(run.bold){var strong=document.createElement("strong");strong.appendChild(node);node=strong;}
  if(run.link){var link=document.createElement("a");link.href=run.link;link.target="_blank";link.rel="noopener noreferrer";link.appendChild(node);node=link;}
  parent.appendChild(node);
});}
function previewImage(image){var figure=document.createElement("figure");figure.className="news-block-image";var picture=document.createElement("img");picture.src=image.url;picture.alt=image.alt_text||image.caption||"Article image";picture.loading="lazy";figure.appendChild(picture);if(image.caption){var caption=document.createElement("figcaption");caption.textContent=image.caption;figure.appendChild(caption);}return figure;}
function previewArticle(){capture();preview.innerHTML="";var article=document.createElement("div");article.className="news-article-body";blocks.forEach(function(block){var node;
  if(block.type==="heading"){node=document.createElement("h"+Math.min(4,Math.max(2,Number(block.level)||2)));node.className="news-block-heading level-"+(block.level||2);node.textContent=block.text||"Heading";}
  else if(block.type==="subheading"){node=document.createElement("p");node.className="news-block-subheading";node.textContent=block.text||"Subheading";}
  else if(block.type==="paragraph"){node=document.createElement("p");appendInline(node,block.content);}
  else if(block.type==="quote"){node=document.createElement("blockquote");node.className="news-block-quote";appendInline(node,block.content);if(block.cite){var cite=document.createElement("cite");cite.textContent=block.cite;node.appendChild(cite);}}
  else if(block.type==="highlight"){node=document.createElement("aside");node.className="news-block-highlight";if(block.title){var title=document.createElement("strong");title.textContent=block.title;node.appendChild(title);}var copy=document.createElement("p");appendInline(copy,block.content);node.appendChild(copy);}
  else if(block.type==="bullet_list"||block.type==="numbered_list"){node=document.createElement(block.type==="bullet_list"?"ul":"ol");node.className="news-block-list";(block.items||[]).forEach(function(item){var li=document.createElement("li");appendInline(li,item);node.appendChild(li);});}
  else if(block.type==="image"&&block.url){node=previewImage(block);}
  else if(block.type==="gallery"){node=document.createElement("div");node.className="news-block-gallery";(block.images||[]).forEach(function(image){if(image.url)node.appendChild(previewImage(image));});}
  else if(block.type==="key_data"){node=document.createElement("dl");node.className="news-key-data";(block.items||[]).forEach(function(item){var card=document.createElement("div");var dt=document.createElement("dt");var dd=document.createElement("dd");dt.textContent=item.label||"";dd.textContent=item.value||"";card.appendChild(dt);card.appendChild(dd);node.appendChild(card);});}
  else if(block.type==="table"){node=document.createElement("div");node.className="news-table-scroll";var table=document.createElement("table");var thead=document.createElement("thead");var headRow=document.createElement("tr");(block.headers||[]).forEach(function(value){var th=document.createElement("th");th.scope="col";th.textContent=value;headRow.appendChild(th);});thead.appendChild(headRow);table.appendChild(thead);var tbody=document.createElement("tbody");(block.rows||[]).forEach(function(row){var tr=document.createElement("tr");row.forEach(function(value){var td=document.createElement("td");td.textContent=value;tr.appendChild(td);});tbody.appendChild(tr);});table.appendChild(tbody);node.appendChild(table);}
  else if(block.type==="divider"){node=document.createElement("hr");node.className="news-block-divider";}
  else if(block.type==="youtube"||block.type==="instagram"){node=document.createElement("section");node.className="news-embed-block"+(block.type==="instagram"?" news-instagram-block":"");var label=document.createElement("strong");label.textContent=block.type==="youtube"?"YouTube video":"Instagram post";var link=document.createElement("a");link.href=block.url||"#";link.target="_blank";link.rel="noopener noreferrer";link.textContent=block.url||"Add a valid URL";node.appendChild(label);node.appendChild(document.createElement("br"));node.appendChild(link);}
  if(node)article.appendChild(node);
});preview.appendChild(article);preview.hidden=false;preview.scrollIntoView({behavior:"smooth",block:"start"});
}
root.addEventListener("click",function(event){
  var mediaAdd=event.target.closest("[data-add-media-block]");if(mediaAdd){capture();blocks.push(blank(mediaAdd.dataset.addMediaBlock));render();setStatus(mediaAdd.dataset.addMediaBlock==="youtube"?"YouTube video block added. Paste a public video URL.":"Instagram block added. Paste a public post or reel URL.");return;}
  var add=event.target.closest("[data-add-block]");if(add){capture();blocks.push(blank(root.querySelector("[data-block-type]").value));render();return;}
  if(event.target.closest("[data-convert-paste]")){convertPaste();return;}
  if(event.target.closest("[data-preview]")){previewArticle();return;}
  var card=event.target.closest(".news-block-editor");if(!card)return;var index=Number(card.dataset.index);
  if(event.target.closest("[data-remove]")){capture();blocks.splice(index,1);render();return;}
  var move=event.target.closest("[data-move]");if(move){capture();var target=move.dataset.move==="up"?index-1:index+1;if(target>=0&&target<blocks.length){var item=blocks.splice(index,1)[0];blocks.splice(target,0,item);render();}return;}
  var format=event.target.closest("[data-format]");if(format){var editable=card.querySelector(".news-contenteditable");editable.focus();if(format.dataset.format==="link"){var url=window.prompt("HTTPS link URL");if(url)document.execCommand("createLink",false,url);}else document.execCommand(format.dataset.format,false,null);capture();return;}
  var upload=event.target.closest("[data-upload]");if(upload){var picker=card.querySelector("[data-files]")||document.createElement("input");picker.type="file";picker.accept="image/png,image/jpeg,image/webp";picker.multiple=upload.dataset.upload==="gallery";picker.onchange=function(){uploadFiles(Array.from(picker.files||[]),blocks[index],upload.dataset.upload==="gallery");};picker.click();}
});
root.querySelector("form").addEventListener("submit",function(){capture();});
blocks=initialBlocks();render();
})();
