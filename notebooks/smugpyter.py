# code from:
# https://github.com/speedenator/smuploader/blob/master/bin/smregister
# https://github.com/kevinlester/smugmug_download/blob/master/downloader.py
# modified for python 3.6/jupyter environment - modifications assisted by 2to3 tool 

from rauth.service import OAuth1Service
from string import ascii_letters, digits
import requests
import http.client
import httplib2
import hashlib
import urllib.request, urllib.parse, urllib.error
import time
import sys
import os
import json
import configparser
import re
import shutil
import csv

class SmugPyter(object):
    
    smugmug_api_base_url = 'https://api.smugmug.com/api/v2'
    smugmug_upload_uri = 'http://upload.smugmug.com/'
    smugmug_base_uri = 'http://api.smugmug.com'
    smugmug_request_token_uri = 'http://api.smugmug.com/services/oauth/1.0a/getRequestToken'
    smugmug_access_token_uri = 'http://api.smugmug.com/services/oauth/1.0a/getAccessToken'
    smugmug_authorize_uri = 'http://api.smugmug.com/services/oauth/1.0a/authorize'
    smugmug_api_version = 'v2'
    
    # cannot create SmugPyter objects if this file is missing
    smugmug_config = os.path.join(os.path.expanduser("~"), '.smugpyter.cfg')

    def __init__(self, verbose=False):
        """
        Constructor. 
        Loads the config file and initialises the smugmug service
        """

        self.verbose = verbose
        self.argument_default = 'images'
        self.local_directory = 'c:/SmugMirror/'
        
        config_parser = configparser.RawConfigParser()
        config_parser.read(SmugPyter.smugmug_config)
        try:
            self.username = config_parser.get('SMUGMUG','username')
            self.consumer_key = config_parser.get('SMUGMUG','consumer_key')
            self.consumer_secret = config_parser.get('SMUGMUG','consumer_secret')
            self.access_token = config_parser.get('SMUGMUG','access_token')
            self.access_token_secret = config_parser.get('SMUGMUG','access_token_secret')
            self.local_directory = config_parser.get('SMUGMUG','local_directory')
        except:
            raise Exception("Config file is missing or corrupted. Run 'python smugpyter.py'")

        self.smugmug_service = OAuth1Service(
            name='smugmug',
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            request_token_url=self.smugmug_request_token_uri,
            access_token_url=self.smugmug_access_token_uri,
            authorize_url=self.smugmug_authorize_uri)
            
        self.request_token, self.request_token_secret = self.smugmug_service.get_request_token(method='GET', params={'oauth_callback':'oob'})
        self.smugmug_session = self.smugmug_service.get_session((self.access_token, self.access_token_secret))
        
    def get_authorize_url(self):
        """
        Returns the URL for OAuth authorisation.
        """
        self.request_token, self.request_token_secret = self.smugmug_service.get_request_token(method='GET', 
                                                                                               params={'oauth_callback':'oob'})
        authorize_url = self.smugmug_service.get_authorize_url(self.request_token, Access='Full', Permissions='Add')
        return authorize_url

    def get_access_token(self, verifier):
        """
        Gets the access token from SmugMug.
        """
        self.access_token, self.access_token_secret = self.smugmug_service.get_access_token(method='POST',
                                    request_token=self.request_token,
                                    request_token_secret=self.request_token_secret,
                                    params={'oauth_verifier': verifier})                            
        return self.access_token, self.access_token_secret

    def request_once(self, method, url, params={}, headers={}, files={}, data=None, header_auth=False):
        """
        Performs a single request.
        """
        if self.verbose == True:
            print('\nREQUEST:\nmethod='+method+'\nurl='+url+'\nparams='+str(params)+'\nheaders='+str(headers))
            if len(str(data)) < 300:
                print("data="+str(data))

        response = self.smugmug_session.request(url=url,
                        params=params,
                        method=method,
                        headers=headers,
                        files=files,
                        data=data,
                        header_auth=header_auth)
        if self.verbose == True:
            print('RESPONSE DATA:\n' + str(response.content)[:100] + (" ... " + str(response.content)[-100:] if len(str(response.content)) > 200 else ""))
        try:
            data = json.loads(response.content)
        except Exception:
            pass
        return data

    def request(self, method, url, params={}, headers={}, files={}, data=None, header_auth=False, retries=5, sleep=5):
        """
        Performs requests, with multiple attempts if needed.
        """
        retry_count=retries
        while retry_count > 0:
            try:
                response = self.request_once(method, url, params, headers, files, data, header_auth)
                if ('Code' in response and response['Code'] in [200, 201]) or ("stat" in response and response["stat"] in ["ok"]):
                    return response
            except (requests.ConnectionError, requests.HTTPError, requests.URLRequired, 
                    requests.TooManyRedirects, requests.RequestException, http.client.IncompleteRead) as e:          
                if self.verbose == True:
                    print(sys.exc_info()[0])
            if self.verbose == True:
                print('Retrying (' + str(retry_count) + ')...')
            time.sleep(sleep)
            retry_count -= 1
        print('Error: Too many retries, giving up.')
        sys.exit(1)

    ## Album

    def get_albums(self):
        """
        Get a list of all albums in the account.
        """
        if self.verbose == True:
            print("Getting albums")
        
        albums = []
        start = 1
        stepsize = 500
        while(True):
            params = {'start': start, 'count': stepsize}
            response = self.request('GET', self.smugmug_api_base_url + "/user/"+self.username+"!albums", 
                                    params=params, headers={'Accept': 'application/json'})

            for album in response['Response']['Album']:
                albums.append({"Title": album['Title'], "Uri": album["Uri"], "AlbumKey": album["AlbumKey"]})

            if 'NextPage' in response['Response']['Pages']:
                start += stepsize
            else:
                break
        return albums   

    def get_album_names(self):
        """
        Return list of album names.
        """
        albums = self.get_albums()
        album_names = [a["Title"] for a in albums]
        return album_names

    def get_album_id(self, album_name):
        """
        Get an album id.
        """
        if album_name == None:
            raise Exception("Album name needs to be defined")

        album_id = None
        for album in self.get_albums():
            if SmugPyter.decode(album['Title']) == SmugPyter.decode(album_name):
                album_id = album['AlbumKey']
                break
        return album_id   
    
    def get_image_date(self, imagemeta_data):
    
        """
        Get an image date.
    
        There are a number of SmugMug image dates to choose from. The dates
        obtained from the (images) or (geomedia) options refer to upload and 
        adjustment times. The original image date must be extracted from the image
        metadata EXIF/IPTC. Sadly, the metadata tag is nonstandard and there are a 
        number of choices. This function attempts to pick the best available 
        original image date.
    
        """

        if 'DateTimeCreated' in imagemeta_data:
            original_date = imagemeta_data['DateTimeCreated']
            if ('' == original_date) and 'DateTimeModified' in imagemeta_data:
                original_date = imagemeta_data['DateTimeModified']
        elif 'DateTimeOriginal' in imagemeta_data:
            original_date = imagemeta_data['DateTimeOriginal']
        else:
            original_date = ''
   
        return original_date

    def get_album_images(self, album_id, argument='images'):
        """
        Get a list of images in an album.
        
        The (argument) parameter selects various API options. For
        example to select all the geotagged images in an album do:
        
            smugmug = SmugPyter()
            smugmug.get_album_images('gLd4hT', "geomedia")
        """
        if album_id == None:
            raise Exception("Album ID must be set to retrieve images")

        images = []
        start = 1
        stepsize = 500
        while(True):
            params = {'start': start, 'count': stepsize}
            response = self.request('GET', self.smugmug_api_base_url + "/album/"+album_id+"!" + argument, 
                                    params=params, headers={'Accept': 'application/json'})
            
            # extract the metadata I care about
            for image in (response['Response']['AlbumImage'] if 'AlbumImage' in response['Response'] else []): 
                clean_caption = self.purify_smugmug_text(image["Caption"])
                clean_keywords = self.purify_smugmug_text(image["Keywords"])
                images.append({"ImageKey": image['ImageKey'], "FileName": image["FileName"], 
                               "Latitude": image["Latitude"], "Longitude": image["Longitude"], 
                               "Altitude": image["Altitude"], 
                               "OriginalHeight": image["OriginalHeight"], "OriginalWidth": image["OriginalWidth"],
                               "Date": image["Date"], "LastUpdated": image["LastUpdated"], "Uri": image["Uri"], 
                               "ThumbnailUrl": image["ThumbnailUrl"], 
                               "Keywords": clean_keywords, "Caption": clean_caption})

            if 'NextPage' in response['Response']['Pages']:
                start += stepsize
            else:
                break
                
        # return images sorted by file name - this helps reduce 
        # spurious line differences in TAB delimited files 
        images = sorted(images, key = lambda k: k["FileName"])
        return images

    def get_album_image_names(self, album_images): 
        """
        Get a list of {ImageKey, FileName} dictionaries for (album_images).
        
            smugmug = SmugPyter()
            album_images = smugmug.get_album_images('XghWcL')
            smugmug.get_album_image_names(album_images)
        """
        image_names = [{"ImageKey": i["ImageKey"], "FileName": i["FileName"]} for i in album_images]
        return image_names
       
    def get_album_image_captions(self, album_images):
        """
        Get a list of {ImageKey, Caption} dictionaries for (album_images).
        """
        image_captions = [{"ImageKey": i["ImageKey"], "Caption": i["Caption"]} for i in album_images]
        return image_captions
      
    def get_latitude_longitude_altitude(self, album_images):
        """
        Get a list of {ImageKey, (Latitute,Longitude,Altitude)} dictionaries for (album_images).
        """
        images_lba = [{"ImageKey": i["ImageKey"], "LatLongAlt": (i["Latitude"], i["Longitude"], i["Altitude"])} 
                      for i in album_images]
        return images_lba
      
    def get_album_image_real_dates(self, album_images):
        """
        Get a list of {ImageKey, RealDate} dictionaries for (album_images). 
        """
        image_keys = [i["ImageKey"] for i in album_images]
        image_dates = []
        start = 1
        stepsize = 500
        params = {'start': start, 'count': stepsize}
        headers = {'Accept': 'application/json'}
        # this is ugly but I don't see any other way to get the original image EXIF dates
        for key in image_keys:
            response = self.request('GET', smugmug.smugmug_api_base_url + "/image/" + key + "!metadata", 
                                    params=params, headers=headers)
            image_date = self.get_image_date(response['Response']['ImageMetadata'])
            image_dates.append({"ImageKey": key, "RealDate": image_date})    
        return image_dates
    
    def get_image_download_url(self, image_id):
        """
        Get the link for dowloading an image.
        """
        response = self.request('GET', self.smugmug_api_base_url + "/image/"+image_id+"!download", 
                                headers={'Accept': 'application/json'})
        return response['Response']['ImageDownload']['Url']
    
    def create_nice_name(self, name):
        return "-".join([re.sub(r'[\W_]+', '', x) for x in name.strip().split()]).title()
    
    def create_album(self, album_name, password = None, folder_id = None, template_id = None):
        """
        Create a new album.
        """
        data = {"Title": album_name, "NiceName": self.create_nice_name(album_name), 
                'OriginalSizes' : 1, 'Filenames' : 1}
        if password != None:
            data['Password'] = password

        if template_id != None:
            data["AlbumTemplateUri"] = template_id
            data["FolderUri"] = "/api/v2/folder/user/"+self.username+("/"+folder_id if folder_id != None else "")+"!albums"
            response = self.request('POST', 
                                    self.smugmug_api_base_url + "/folder/user/"+self.username+("/"+folder_id if folder_id != None else "")+"!albumfromalbumtemplate", 
                                    data=json.dumps(data), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
        else:
            response = self.request('POST', 
                                    self.smugmug_api_base_url + "/folder/user/"+self.username + ("/"+folder_id if folder_id != None else "") + "!albums", 
                                    data=json.dumps(data), 
                                    headers={'Accept': 'application/json', 'Content-Type': 'application/json'})

        if self.verbose == True:
            print(json.dumps(response))

        return response

    def get_album_info(self, album_id):
        """
        Get info for an album.
        """
        if self.verbose == True:
            print("Getting albums")
            
        response = self.request('GET', self.smugmug_api_base_url + "/album/"+album_id, 
                                headers={'Accept': 'application/json'})
        return response["Response"]["Album"]

        album_info = dict()
        album_key = self.get_album_key(album_id)
        response = self.request('GET', self.smugmug_api_uri, params={'method':'smugmug.albums.getInfo', 
                                                                     'AlbumID':album_id, 'AlbumKey':album_key})
        info['album_id'] = response['Album']['id']
        info['album_name'] = response['Album']['Title']
        info['category_id'] = response['Album']['Category']['id']
        info['category_name'] = response['Album']['Category']['Name']
        return info

    ## Folders
    
    def get_child_node_uri(self, node_id):
        """
        Get child node uri.
        """ 
        response = self.request('GET', self.smugmug_api_base_url + "/node/" + node_id, 
                                 headers={'Accept': 'application/json'})
        uri = response["Response"]["Node"]["Uris"]["ChildNodes"]["Uri"]
        return uri
        
    def mirror_folders_offline(self, root_uri, root_dir):
        root_uri = (self.smugmug_base_uri + '%s') % root_uri
        if not '!children' in root_uri:
            root_uri += '!children'
        #print('url = ' + root_uri)
        response = self.request('GET', root_uri, headers={'Accept': 'application/json'})
        for node in response["Response"]["Node"]:
            name = self.extract_alphanum(node["Name"])
            path = '%s/%s' % (root_dir, name)
            #print(path)
            os.makedirs(path, exist_ok=True)
            if node["Type"] == 'Folder':
                self.mirror_folders_offline(node["Uri"], path)
            elif node['Type'] == 'Album':
                print('visiting album ' + name)
                uri = node["Uris"]["Album"]["Uri"]
                album_id = uri.split('/')[-1]
                album_images = self.get_album_images(album_id)
                if len(album_images) > 0:
                    manifest_name = "manifest-%s-%s" % (name, album_id)
                    manifest_file = path + "/" + manifest_name + '.txt'
                    #print(manifest_file)
                    self.write_album_manifest(manifest_file, album_images)
            
                #Queue for download
                #master_albums_list.append(path)
                #dl_queue.put({'node' : node, 'path' : path})
        
        #if 'NextPage' in response['Response']['Pages']:
        #    self.mirror_folders_offline(pages['NextPage'], root_dir)
        
    def download_smugmug_mirror(self):
        """
        Walk SmugMug folders and albums and mirror selected metadata in (self.root_folder).
        """
        root_folder = self.local_directory
        folders = self.get_folders()
        for folder in folders:
            root_uri = self.get_child_node_uri(folder["NodeID"])
            top_folder = self.extract_alphanum(folder["Name"])
            self.mirror_folders_offline(root_uri, root_folder + top_folder)
        print("done")
                     
    def write_album_manifest(self, manifest_file, album_images):
        """
        Write TAB delimited file of SmugMug image metadata.
        """
        keys = album_images[0].keys()
        with open(manifest_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            dict_writer.writerows(album_images)       
           
    def get_folders(self):
        """
        Get a list of folder names under the user.
        Currently supports only top-level folders.
        """
        response = self.request('GET', self.smugmug_api_base_url + "/folder/user/"+self.username+"!folders", 
                                headers={'Accept': 'application/json'})
        folders = []
        for folder in response['Response']['Folder']:
            folders.append({"Name": folder["Name"], 
                            "NodeID": folder["NodeID"], "UrlName": folder["UrlName"]})
        return folders    

    def get_folder_names(self):
        """
        Return list of (top-level) folder names.
        """
        folders = self.get_folders()
        folder_names = [f["Name"] for f in folders]
        return folder_names   

    def get_folder_id(self, folder_name):
        """
        Get category id.
        """
        folder_id = None
        for folder in self.get_folders():
            if folder['Name'] == folder_name:
                folder_id = folder['UrlName']
                break
        return folder_id
    
    # Upload/download

    def upload_image(self, image_data, image_name, image_type, album_id):
        """
        Upload an image.
        """
        response = self.request('POST', self.smugmug_upload_uri,
            data=image_data,
            header_auth = True,
            headers={'X-Smug-AlbumUri': "/api/v2/album/"+album_id, 
                'X-Smug-Version':self.smugmug_api_version, 
                'X-Smug-ResponseType':'JSON',
                'Content-MD5': hashlib.md5(image_data).hexdigest(),
                'X-Smug-FileName':image_name,
                'Content-Length' : str(len(image_data)),
                'Content-Type': image_type})
        return response

    def download_image(self, image_info, image_path, retries=5):
        """
        Download an image from a url.
        """
        count = retries
        image_url = self.get_image_download_url(image_info["ImageKey"])
        image_path_temp = image_path + "_temp"

        while count > 0:
            count -= 1
            # Doing the actual downloading
            image_data = self.smugmug_session.request(url=image_url, method='GET', stream=True).raw
            image_data.decode_content = True
            with open(image_path_temp, 'wb') as f:
                shutil.copyfileobj(image_data, f)
            
            # Checking the image
            image_data_local = SmugMug.load_image(image_path_temp)
            image_md5sum = hashlib.md5(image_data_local).hexdigest()
            image_size = str(len(image_data_local))
            if image_md5sum != image_info['ArchivedMD5']:
                raise Exception("MD5 sum doesn't match.")
            elif image_size != str(image_info['OriginalSize']):
                raise Exception("Image size doesn't match.")
            else:
                os.rename(image_path_temp, image_path)
                break

            if count > 0:
                print("Retrying...")
            else:
                raise Exception("Error: Too many retries.")
                sys.exit(1)

    @staticmethod
    def load_image(image_path):
        """
        Load the image data from a path.
        """
        try:
            image_data = open(image_path, 'rb').read()
            return image_data
        except IOError as e:
            raise "I/O error({0}): {1}".format(e.errno, e.strerror)
        return None
    
    @staticmethod
    def extract_alphanum(in_string):
        return "".join([ch for ch in in_string if ch in (ascii_letters + digits)])
    
    @staticmethod
    def purify_smugmug_text(in_string):
        """
        Convert Smugmug unicode strings to ascii equivalents making non-ascii characters 
        visible as XML escapes. Also convert embedded control character to blanks.
        """
        purify = re.sub(' +', ' ', in_string)
        purify = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', purify)
        return purify.encode('ascii', 'xmlcharrefreplace' ).decode('ascii')
    
    @staticmethod
    def decode(obj, encoding='utf-8'):
        if isinstance(obj, str):
            if not isinstance(obj, str):
                obj = str(obj, encoding)
        return obj
    