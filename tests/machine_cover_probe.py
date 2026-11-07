"""Shared pixel/geometry oracle for the approved single-cover background."""
probe=r'''([w,h,ratio])=>mcRun(()=>{
 const im=gameMachineFortress.backgroundImage,c=document.createElement('canvas');c.width=Math.ceil(w*ratio);c.height=Math.ceil(h*ratio);const g=c.getContext('2d');g.setTransform(ratio,0,0,ratio,0,0);
 const calls=[],original=g.drawImage;g.drawImage=function(image,...a){calls.push({original:image===im,args:a,source:[image.width,image.height],filter:g.filter,alpha:g.globalAlpha});return original.call(g,image,...a)};gameMachineFortress.drawBackground(g,w,h);g.drawImage=original;
 const ref=document.createElement('canvas');ref.width=c.width;ref.height=c.height;const r=ref.getContext('2d');r.setTransform(ratio,0,0,ratio,0,0);
 const scale=Math.max(w/im.naturalWidth,h/im.naturalHeight),dw=im.naturalWidth*scale,dh=im.naturalHeight*scale,x=(w-dw)/2,y=(h-dh)/2;r.drawImage(im,x,y,dw,dh);
 const a=g.getImageData(0,0,c.width,c.height).data,b=r.getImageData(0,0,c.width,c.height).data;let minAlpha=255,centerDiff=0;const colors=new Set();
 for(let py=0;py<c.height;py++)for(let px=0;px<c.width;px++){const i=(py*c.width+px)*4;minAlpha=Math.min(minAlpha,a[i+3]);for(let q=0;q<4;q++)centerDiff=Math.max(centerDiff,Math.abs(a[i+q]-b[i+q]));if(px===0||py===0||px===c.width-1||py===c.height-1)colors.add([a[i],a[i+1],a[i+2],a[i+3]].join());}
 return {size:[w,h],ratio,canvas:[c.width,c.height],source:[im.naturalWidth,im.naturalHeight],cover:[x,y,dw,dh],visibleSource:[-x/scale,-y/scale,w/scale,h/scale],calls,minAlpha,centerDiff,centerPixels:c.width*c.height,perimeterColors:colors.size};
})'''
def check_background(row):
 w,h=row['size'];scale=max(w/1672,h/941);expected=[(w-1672*scale)/2,(h-941*scale)/2,1672*scale,941*scale]
 assert row['source']==[1672,941] and row['centerDiff']==0 and row['centerPixels']>1000 and row['minAlpha']==255,row
 assert len(row['calls'])==1 and row['calls'][0]['original'] and row['calls'][0]['alpha']==1 and row['calls'][0]['filter']=='none',row
 assert len(row['calls'][0]['args'])==4 and all(abs(a-b)<1e-6 for a,b in zip(row['calls'][0]['args'],expected)),row
 assert row['perimeterColors']>20 and expected[2]>=w-1e-6 and expected[3]>=h-1e-6,row
