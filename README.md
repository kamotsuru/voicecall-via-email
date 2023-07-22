# Migration from twilio to vonage
## 0.  Motivation
Twilio Japan closed their existing user accounts for any personal use, including me, Oct. 2022, then I had decided my application, which originally sends SMS triggered by receiving email, to migrate from Twilio to Vonage.

This article touches on two Vonage applications:

i. Sending SMS

ii. Voice calling
## 1.  Create a Vonage account
Click "Login" at upper right of [Vonage Japan site](https://www.vonagebusiness.jp/l/)
![vonagelogin1.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/e2f1c56f-f555-7168-a338-1e571c5c2613.png)
Then, click "Communication API Login"
![vonagelogin2.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/3e325d6a-338d-f7ab-9c18-47da680cb3bc.png)
Next, click "Sign up" to create a free account to which 10 euro credit is assigned. The free account has some limitations, but it's enough for my application to check if it works.

I used Safari on Mac for registering my account, but the site got not reacting during the procedure. So, I changed the web browser to Iron(Chrome), then it works.
![vonagelogin3.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/87b804f4-fcfe-6038-4a09-2b3a60d80666.png)
## 2.  Sending SMS by API
As a test, I sent an SMS by [python](https://github.com/vonage/vonage-python-code-snippets/blob/master/sms/send-an-sms.py#L15-L16) referred by [Send an SMS](https://developer.vonage.com/messaging/sms/code-snippets/send-an-sms) at Developer site.
```{.line-number}
import vonage

client = vonage.Client(key="your key", secret="your secret")
sms = vonage.Sms(client)

responseData = sms.send_message(
    {
        "from": "Vonage APIs",
        "to": "8180xxxxxxxx",
        "text": "A text message sent using the Nexmo SMS API",
        }
    )
if responseData["messages"][0]["status"] == "0":
    print("Message sent successfully.")
else:
    print("status = "+responseData["messages"][0]["status"])
    print("Message faild with error: "+responseData['messages'][0]['error-text'])
```
The values of "key" and "secret" in 3rd line are assigned as those of "API Key" and "API secret" in "API Settings" at the left side bar on the dashboard.

Although the value of "from" in 8th line is "Vonage APIs", we can send an SMS to cell phone numbers of Japan careers, but cannot send to cell phone numbers to US and Canadian careers, because of the reason described later.
![key.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/ebec7804-dbc1-ec94-f9d5-e17d09172612.png)
My cell phone which career is au by KDDI, Japan, received an SMS as below. The footer "[FREE SMS DEMO, TEST MESSAGE]" is added to each SMS message during free account.
<div  align="center">
<img width="300" alt="IMG_50D17B8DA058-1.jpeg" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/a71bcbe2-67f9-c727-83f2-4fd30c51e03f.jpeg">
</div>

## 3.  Migration of SMS sending from twilio
The python [code](https://github.com/jpf/sms-via-email) referred by [Send And Receive SMS Messages via Email with Twilio and SendGrid](https://www.twilio.com/blog/send-and-receive-sms-messages-via-email-with-twilio-and-sendgrid-html) was modified as [app.py](https://github.com/kamotsuru/twilio2vonage/blob/main/app.py). The whole procedure to send SMS triggered by receiving email with SendGrid, heroku and your own DNS domain is described in the above site, Send And Receive SMS Messages via Email with Twilio and SendGrid.

I deployed this code on render.com and uses AWS Route 53 as DNS.

Twilio requires "+" at the beginning of a phone number, but Vonage rejects this as an error, then roughly replaces "+" with "" at 219th line.
## 4.  Buy a phone number
As above wrote, we can send SMS to Japanese cell phone without a phone number, but it costs 0.07euro(9.9 JPY)/message. US career to US career, my Google Voice phone number, costs 0.0062euro(0.9JPY)/message at one tenth, and the purchase and maintenance of a phone number costs 0.9euro(127JPY)/month, then sending 15 messages/month can be above break-even.
So, I upgraded my free account by registering a credit card, and purchased a phone number by US career.

From "Buy Numbers", we can choose and buy a phone number coming up after selecting "SMS" Feature and putting 4-digit.
![buy.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/5f382410-ede7-e983-cac8-f39dd3f7f1ca.png)
As noticed by "Buy a 10DLC number and link it to a brand and campaign", to reduce spam SMS, an SMS sender must register the followings:
- Your company name
- The country you’re registered in
- The type of company you are
- Your tax or EIN number
- Your company’s website
- SMS campaign name, description, and use case
- Sample messages from your campaign
- Contact information

See [A2P 10 DLC - The Ultimate Guide](https://www.salesmessage.com/blog/a2p-10-dlc-ultimate-guide) .

At the beginning of Dec. 2022, I had been unable to send SMS, then asked Vonage support what happened. The reply is that 10DLC was started to strictly apply as follows:

>I have checked the reported logs and noticed that your messages from LVN 1xxxxxxxxxx to US numbers have been rejected on our hub with the reason "Illegal sender address for US destination", the blocking you are experiencing to U.S networks is due to industry-wide regulations. To ensure compliance, all traffic originating from non-10DLC or toll-free numbers will be blocked beginning on December 1st.
As mentioned in our article The US has very specific messaging restrictions and LVN can be used to only p2p traffic with exemption from network operators all SMS sent to the US must originate from a registered toll-free, 10 DLC, or short code that is associated with your Vonage account.
## 5. Voice calling
I finally decided to use voice calling. The 1st line of email which I forwarded as an SMS costs 0.00084667euro/4sec...
### 5.1. Get "Applicaiton ID"
From "Make a Voice Call" under "Getting Started" at the left side bar, "APPLICATION_ID" and "APPLICATION_PRIVATE_KEY" were generated when pushing "Create application", and the latter one is downloadable as "private.key".
![Screen Shot 2022-12-08 at 17.36.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/53e17f61-3802-0c89-1722-3a8c484b2a7a.png)

These are reflected at "Applications".
![Screen Shot 2022-12-08 at 17.36.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/8afb8849-f842-8a5d-1bec-a102f21717e0.png)

We have to link these to an already purchased phone number. The "Unlink" button was "Link" before pushed and linked. 
![Screen Shot 2022-12-09 at 20.58.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/cb42b882-900f-b24c-98b9-0478678d7451.png)
### 4.2. Code
I modified the above code to [app.py](https://github.com/kamotsuru/twilio2vonage/blob/main/voiceapp.py). The following just shows some main parts. The voice can be chosen  reffering [Voice API > Text to Speech](https://developer.vonage.com/voice/voice-api/guides/text-to-speech)
```
vonage_client = vonage.Client(key=konf.vonage_api_key,
                              secret=konf.vonage_api_secret,
                              application_id=konf.vonage_application_id,
                              private_key="/etc/secrets/VONAGE_APPLICATION_PRIVATE_KEY")

vonage_voice = vonage.Voice(vonage_client)

responseData = vonage_voice.create_call({      
	'from': {'type': 'phone', 'number': lookup.phone_for_email(email_from).replace('+','')},       
	'to': [{'type': 'phone', 'number': email_to_phone(envelope['to'][0]).replace('+','')}],                                             
        'ncco': [
            {
                "action": "talk",
                "text": lines[0].split('に')[1],
                "language": "ja-JP",
                "style": 2
            }
        ]
    })

return responseData["status"]
```
### 4.3. Set "APPLICATION_ID" as an environment variable at render.com
From "Environment" at the left side bar on render.com, I set "APPLICATION_ID" as an environment variable "VONAGE_APPLICATION_ID" and pasted the content of "private.key" as a file with the name of "VONAGE_APPLICATION_PRIVATE_KEY". The file is deployed under "/etc/secrets" on my application server at render.com.
![Screen Shot 2022-12-08 at 17.50.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/117100/ce5be564-3846-c2a7-5b2d-1ba00af76602.png)
## 6. Epilogue
I sincerely expect Vonage not to shut out any personal user as Twilio did so. By the way, Vonage has [become](https://www.ericsson.com/ja/press-releases/2022/7/ericsson-completes-acquisition-of-vonage) one of subsidiary of Ericsson.
