def update_all_sample_images(self, root):
        """
        Scan all manifest files in local directories and download sample
		images listed in manifest files that are not already present. 
        """
        return self.scan_do_local_files(root, func_do=self.download_album_sample_images, yammer=False)
		

def scan_do_local_files(self, root, *, func_do=None, pattern='manifest-', alist_filter=['txt'], yammer=True):
        total_images, total_changes = 0 , 0
        for r,d,f in os.walk(root):
            for file in f:
                if file[-3:] in alist_filter and pattern in file:
				    image_count , change_count = 0 , 0
                    file_name = os.path.join(root,r,file)
					if func_do is not None:
                        image_count , change_count = func_do(file_name)
					if yammer:
					    print(file_name)
                    total_images += image_count
					total_changes += change_count
        return (total_images, total_changes)
