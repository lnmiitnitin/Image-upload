from rest_framework import generics
from django.views.generic.base import View
from django.http import HttpResponseRedirect, HttpResponse
import json
import requests
import base64
from django.views.decorators.csrf import csrf_exempt
from celery import task,group
from celery import uuid
import celery
from datetime import datetime
import redis
import time
from api.settings import REDIS_HOST, REDIS_PORT, REDIS_DB
try:
    redis_conn = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
except Exception as e:
    redis_conn = None

class GetUploadStatusView(View):
    """
    View return the status of the job submitted 
    input: Job_id (job_id returned from the image upload async task)   
    
    response:
	{
	"id": "55355b7c-9b86-4a1a-b32e-6cdd6db07183",
	"created": "2017-12-22T16:48:29+00:00",
	"finished": null,
	"status": "in-progress",
		"uploaded": {
		"pending": [
			"https://i.imgur.com/rsD0RUq.jpg",
		],
		"complete": [
			"https://i.imgur.com/gAGub9k.jpg",
			"https://i.imgur.com/skSpO.jpg"
		],
		"failed": [
		]
	    }
	}

 
    """
    
    def get(self,request,job_id):
        result = {}
	start_time = None
	result["id"] = job_id
	result["created"] = start_time
	result["finished"] = None
	result["status"] = None
	result["uploaded"] = {}
	result["uploaded"]["complete"] = []
	result["uploaded"]["failed"] = []
	result["uploaded"]["pending"] = []
 	original_url = None
	max_finish_time = 0 
	if redis_conn and job_id:
	    output = redis_conn.get(job_id) # Get parent job id 
	    if output:
		output,start_time,urls = eval(output) # Get parent job child id corresponding to seperate urls, job publish time, original urls
	        result["created"] = datetime.fromtimestamp(start_time).isoformat()  	
		for index,child_id in enumerate(output):
		    original_url = urls[index]
		    job_output = redis_conn.lrange(child_id,0,-1) # Get output response from server after upload
		    if job_output:
		        job_response = eval(job_output[0])
			status = job_response.get('status') # job status
			response_data = job_response.get("data")
			if response_data:
			    image_link = response_data.get('link')  #uploaded url link on imgur 
			    finished_time = response_data.get('datetime')  # finished time
			    if finished_time > max_finish_time:
				max_finish_time  = finished_time  # calculate last finish time for all jobs 
			    if status == 200:
				result["uploaded"]["complete"].append(image_link)
			    else:
				result["uploaded"]["failed"].append(original_url) # append urls
		    else:
			result["uploaded"]["pending"].append(original_url)
		# if length of total urls and ( successful and failed urls) equals then job is complete
	        if len(result["uploaded"]["complete"]) + len(result["uploaded"]["failed"])  == len(output):
	            result["status"] = "complete"
	            result["finished"] = datetime.fromtimestamp(max_finish_time).isoformat()	 	
	        elif result["uploaded"]["pending"] and (result["uploaded"]["complete"] or result["uploaded"]["failed"]):
	            result["status"] = "in-progress"
	            result["finished"] = None	
	        else:
	            result["status"] = "pending"
		 
		 
	return  HttpResponse(json.dumps(result))

class ListImageView(generics.ListAPIView):
    """
    List all images uploaded on imgur till now.
    input: None
    reponse:
	{
		"uploaded": [
			"https://i.imgur.com/gAGub9k.jpg",
			"https://i.imgur.com/skSpO.jpg"
		]
	}	 
   
    """
    def get(self,request):
        image_list = []

	image_list = redis_conn.lrange("uploaded_images",0 ,-1)
		
        result = {
            "uploaded": image_list,
        }
	return  HttpResponse(json.dumps(result))


class UploadImagesView(View):
    """
    upload images on imgur site
    img = requests.post(
		'https://api.imgur.com/3/image',
		 headers = {'Authorization': 'Client-ID c70296d83bd6f79'},
		 data = {
			'key': '80a414ca3ca0d34aff8028356eb6ba04d0d79543',
			'title': 'test',
			'image': encoded_string}
		)
    input: urls
	{
		"urls": [
			"https://farm3.staticflickr.com/2879/11234651086_681b3c2c00_b_d.jpg",
			"https://farm4.staticflickr.com/3790/11244125445_3c2f32cd83_k_d.jpg"
		]
	}
    response:
	{
		"jobId": "55355b7c-9b86-4a1a-b32e-6cdd6db07183",
	}	 

    """

    def post(self,request):
	resp = {"result": "failure"}
	urls = self.request.POST.get('urls','')
	
	urls = eval(urls)
        urls = set(urls)
	urls = list(urls)
	child_id_list = []
	if urls:
	    parent_id = uuid()
	    start_time = int(time.time())
	    # for every urls create async job and store child jobs and time in redis 
	    for url in urls:
	        child_id = uuid()
		child_id_list.append(child_id)
	        image_upload_async.apply_async((url,child_id),task_id=child_id)
	    
	    if redis_conn:
		redis_conn.set(parent_id,(child_id_list,start_time,urls))

        return  HttpResponse(json.dumps(parent_id))

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UploadImagesView, self).dispatch(*args, **kwargs)

@task(default_retry_delay=30, max_retries=2, ignore_result=False)
def image_upload_async(url,child_id):
    """
    upload image async manner

    input: image_url
	   child id   # child id is unique id of job for a single url 
    response:
 	   None
   

    """
    imgur_url = 'https://api.imgur.com/3/image'
    headers = {'Authorization': 'Client-ID {}'.format('c70296d83bd6f79')}
    data = {
	     'key': "{}".format('80a414ca3ca0d34aff8028356eb6ba04d0d79543'),
	    }
     

    if url:
	start_time = int(time.time()) 
	response = requests.get(url)
	encoded_string = base64.b64encode(response.content)
	data['image'] = encoded_string
	data["title"] = "test-1"    # update title
	resp = requests.post(
			imgur_url,
			headers=headers,
			data=data
	)
	j_data = json.loads(resp.text)
        redis_conn.rpush(child_id,j_data)
	if j_data.get('status') == 200: # if reponse is successful update link of image in redis
	    redis_conn.rpush("uploaded_images",j_data.get("data").get("link"))
