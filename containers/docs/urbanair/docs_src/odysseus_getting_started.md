# Project Odysseus

## Introduction

One of the key UK policies in tackling the coronavirus crisis has been to try and ‘flatten the curve’ through social distancing and evidence is beginning to show these may be influencing the number of total cases within London. Furthermore, it's now necessary to start designing strategies for exiting lockdown in a staged, principled, and data driven manner that will restore the economy and our way of life.

This project aims to bring together multiple large-scale and heterogeneous datasets capturing mobility, transportation and traffic activity over the city of London to better understand “busyness” and enable targeted interventions and effective policy-making. The team from the Turing's Data Centric Engineering programme, sponsored by the Lloyd's Register Foundation, will work together with researchers from the University of Warwick, UCL and University of Cambridge to develop models, infrastructure and machine learning algorithms for understanding how and when busyness is changing across the capital in the wider context of Covid-19.

The project is codenamed “Odysseus” because Corona is also known as the “Cyclops' eye”.

More information is available on the [project page](https://www.turing.ac.uk/research/research-projects/project-odysseus-understanding-london-busyness-and-exiting-lockdown).

REST API documentation is available for both [project Odysseus](https://urbanair.turing.ac.uk/odysseus/docs) and the greater [UrbanAir](https://urbanair.turing.ac.uk/docs) air quality forecasts.

## Live map

A dashboard displaying some of the primary outputs of the camera work from Project Odysseus is available at [urbanair.turing.ac.uk/odysseus/map](https://urbanair.turing.ac.uk/odysseus/map).

## New footage sources
### Getting Started
The typical process for including your footage into our detection framework is to first contact the project developers at [urbanair@turing.ac.uk](mailto:urbanair@turing.ac.uk) to evaluate current processing capacity and confirm your feeds meet the following requirements:

 - Maximum resolution of Half D1 (720x288 PAL / 720x240 NTSC)
 - Minimum frame rate of 1Hz (1 FPS)
 - May be compressed as either MP4 or MKV format
 - Subject to a minimum 31 day data retention period

Once we have confirmed your feeds are compatible (or we have written a conversion module), the next step is to begin automatically uploading into the pipeline.

### Pipeline
UrbanAir is built upon Microsoft's Azure platform, hence we require footage to be uploaded to [Azure Storage Containers](https://docs.microsoft.com/en-us/azure/storage/common/storage-account-overview). A [blob](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction) container will be created for you with a connection mechianism similar to FTP via a Shared Access Signature ([SAS](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview)), it should look like this:
```
https://dssg.blob.core.windows.net/footagesubset?sp=rl&st=2020-05-01T00:00:00Z&se=2020-06-01T00:00:00Z&sv=2019-12-12&sr=c&sig=AcfrzCWkcTwadOFe6SCatMxG51Gsd1BYM8QcYOLPqvQ%3D
```

This can be accomplished using any of the supported Azure APIs, presently supported are [Python](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python), [Java](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-java), [JavaScript](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-nodejs), [.NET](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-dotnet), [Go](), [PHP](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-php?tabs=windows), [Ruby](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-ruby), [Xamarin](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-xamarin) and more directly with [PowerShell](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-powershell) and [Azure CLI](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-cli).

### Python upload example 
```python
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# Create connection client with provided URL & SAS token
blob_service_client = BlobServiceClient(account_url="https://cleanair.blob.core.windows.net", credential="<demo>")

# Create a file in local data directory to upload and download
local_path = "./footage"
local_file_name = "quickstart_" + str(uuid.uuid4()) + ".mp4"
upload_file_path = os.path.join(local_path, local_file_name)

# Create a blob client using the local file name as the name for the blob
blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

# Upload the created file
with open(upload_file_path, "rb") as data:
    blob_client.upload_blob(data)
```

### Scheduling
Once a script is managing the uploads has been tested, please decide a schedule on which to upload. Presently, we're operating on continuous feeds with processing scheduled every 30 minutes from 0500 BST - 2100 BST, with roughly 300 cameras processed within the following 36 minutes, resulting in the longest delay nearing 66 minutes from real-time.