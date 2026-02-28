~/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps
i want to copy the labcastarr folder to /Users/oliver/Downloads/labcastarr and make sure it gets copy correctly

I'll help you copy the labcastarr folder to the Downloads directory and verify it was copied correctly. Let me first check if the labcastarr folder exists in your current directory, then copy it and verify the copy.
ls -la labcastarr

Great! I can see the labcastarr folder exists and contains various files and subdirectories. 
Now I'll copy it to the Downloads directory using cp -R (recursive copy) and then verify the copy was successful.
cp -R labcastarr /Users/oliver/Downloads/labcastarr

Now let me verify the copy was successful by checking if the folder exists in Downloads and comparing the contents:
ls -la /Users/oliver/Downloads/labcastarr

Perfect! Now let me do a more thorough verification by comparing the file counts and sizes between the source and destination to make sure everything was copied correctly:
````
echo "Source folder:" && find labcastarr -type f | wc -l && echo "files found" && echo "" && echo "Destination folder:" && find /Users/oliver/Downloads/labcastarr -type f | wc -l && echo "files found"
Source folder:
   39203
files found

Destination folder:
   39203
files found
```

Excellent! Let me also check the total size of both directories to ensure they match:
Perfect! The copy operation was successful. Here's a summary of what was accomplished:
```
echo "Source folder size:" && du -sh labcastarr && echo "" && echo "Destination folder size:" && du -sh /Users/oliver/Downloads/labcastarr
Source folder size:
819M	labcastarr

Destination folder size:
819M	/Users/oliver/Downloads/labcastarr
```

✅ Copy completed successfully!

Verification results:
•  Source location: /Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr
•  Destination location: /Users/oliver/Downloads/labcastarr
•  Files copied: 39,203 files (identical count)
•  Total size: 819M (identical size)
•  All subdirectories and files preserved: Including .git, backend, frontend, docs, web, and all configuration files

The labcastarr folder has been successfully copied to /Users/oliver/Downloads/labcastarr with all files, directories, and permissions preserved. The verification confirms that both the file count and total size match exactly between the source and destination.