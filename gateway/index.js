const express = require('express');
const app = express();
const path = require("path");
const uuid = require('uuid');
const {Storage} = require('@google-cloud/storage');
const fileUpload = require('express-fileupload');
app.use(express.urlencoded({ extended: true }));
app.use(fileUpload({
    useTempFiles : true,
    tempFileDir : '/tmp/'
}));
app.use(express.json());
app.use(express.static(path.join(__dirname,'./public')));

const {ExecutionsClient} = require('@google-cloud/workflows');
const client = new ExecutionsClient();

const projectId = process.env.GOOGLE_CLOUD_PROJECT;
const workflow = 'mail';

const storage = new Storage();

const bucketName = 'yarel-license-plate';

async function uploadImageFile(fileLocation, fileName) {
  await storage.bucket(bucketName).upload(fileLocation, {
    destination: fileName,
  });

  console.log(`${fileName} uploaded to ${bucketName}`);
}

app.get('/', function(req,res){
  res.sendFile(path.join(__dirname,'./public/index.html'));
});

app.post('/', async (req, res) => {
  const name = process.env.NAME || 'World';
  
  if (!req.body.to_email)
    return console.error('missing dest email');

  if (!req.files || Object.keys(req.files).length === 0) {
    return res.status(400).send('No files were uploaded.');
  }

  fileLocation = req.files.carPhoto.tempFilePath;

  imgFileName = uuid.v4() + '.jpg';
  await uploadImageFile(fileLocation, imgFileName).catch(console.error);

  // Execute workflow
  try {
      const createExecutionRes = await client.createExecution({
          execution: {
              argument: JSON.stringify({
                car_photos_bucket_name: bucketName,
                car_photo_file_name: imgFileName,
                to_email: req.body.to_email,
              }),
          },
          parent: client.workflowPath(projectId, 'europe-west4', workflow),
      });
      console.log(`Here: ${createExecutionRes}`);

      const executionName = createExecutionRes[0].name;
      console.log(`Created execution: ${executionName}`);
      res.send(`Request dispatched! Request ID: ${executionName}, Please check your mail!`)
  
  } catch (e) {
      console.error(`Error executing workflow: ${e} ${e.stack}`);
      res.send(`Error in dispatching request!`)
  }
});

if (!projectId)
  return console.error('ERROR: GOOGLE_CLOUD_PROJECT is required.');

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`helloworld: listening on port ${port}`);
});