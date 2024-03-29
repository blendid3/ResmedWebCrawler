import requests
from requests.auth import HTTPBasicAuth
import boto3


class Token():
    def __init__(self, type, text):
        self.text = text
        self.type = type
        pass

    def __eq__(self, other):
        if (self.text == other):
            return True
        else:
            return False;

    def __str__(self):
        return {"text": self.text, "type": self.type}

    def getText(self):
        return self.text

    def getType(self):
        return self.type

    def setText(self, text):
        self.text = text

    def setType(self, type):
        self.type = type


class RTViewTokenizer():
    def __init__(self):
        self.url = "http://rtview.077995606180.priv.dht.live/rtview-emsmon-rtvquery/cache/_rtvMulti?queryCount=3&mq1_cache=EmsQueues&mq1_table=current&mq1_cols=URL%3Bname%3BinboundMessageRate%3BinboundTotalMessages%3BoutboundMessageRate%3BoutboundTotalMessages%3BpendingMessageCount%3BconsumerCount%3Bfailsafe%3BfcMaxBytes%3Bglobal%3BinboundByteRate%3BinboundTotalBytes%3BmaxBytes%3BmaxMsgs%3BoutboundByteRate%3BoutboundTotalBytes%3BoverflowPolicy%3Bsecure%3Bstatic%3Bdescription%3BExpired%3Btime_stamp%3BRateinboundTotalBytes%3BRateinboundTotalMessages%3BRateoutboundTotalBytes%3BRateoutboundTotalMessages%3BpendingMessageSize%3Bexclusive%3BmaxRedelivery%3BPattern%3BreceiverCount&mq1_fcol=URL&mq1_fval=*&mq2_cache=RtvAlertStatsByCategoryIndex&mq2_table=current&mq2_cols=Package%3BCategory%3BAlert%20Index%20Values%3BMaxSeverity%3BAlertCount%3Btime_stamp&mq2_fcol=Package%3BCategory&mq2_fval=Ems%3BQueues&mq3_cache=EmsServerInfo&mq3_table=current&mq3_cols=URL%3BqueueCount&mq3_fcol=URL&mq3_fval=*&fmt=jsonp&to=15&arr=1"
        self.user = 'rtvadmin'
        self.password = 'rtvadmin'
        self.index = 0;
        self.functions = ["try", "catch", "if", "window", "console", "log"]
        self.brackets = "[{()}]"
        self.punctuations = ":,; \n"
        self.bracketsMap = {"}": "{", "]": "[", ")": "("}
        self.getFromWebsite();

    def getFromWebsite(self):
        self.response = requests.get(self.url, auth=HTTPBasicAuth(self.user, self.password)).text;
        assert isinstance(self.response, str)
        return self.response;

    # *****************************************************************************************
    def getTopLetter(self):
        return self.response[self.index]

    def isLetterSpecial(self, letter):
        assert isinstance(letter, str)
        if (letter in self.brackets or letter in self.punctuations):
            return True
        else:
            return False;

    def isFunctions(self, keyword):
        assert isinstance(keyword, str)
        if keyword in self.functions:
            return True;
        else:
            return False;

    def convertStrByType(self, words):
        type = self.getType(words)
        if (type == "number"):
            return float(words)
        elif type == 'boolean':
            if (words == 'True' or words == 'true'):
                return True;
            else:
                return False
        else:
            return words

    def getType(self, words):
        assert isinstance(words, str) or isinstance(words, Token)
        if (isinstance(words, Token)):
            return words.getType();
        if (words[0] == '\"' and words[-1] == "\""):
            return "str"
        if (words in self.functions):
            return "function";
        elif words in self.brackets:
            return "bracket"
        elif words in self.punctuations:
            return "punctuation"
        elif self.isfloat(words):
            return "number"
        elif self.isboolean(words):
            return "boolean"
        else:
            return "unknown"

    def isfloat(self, text):
        assert isinstance(text, str)
        try:
            float(text)
            return True;
        except:
            return False

    def isboolean(self, text):
        assert isinstance(text, str)
        if (text == "false" or text == "true" or text == "True" or text == "False"):
            return True
        else:
            return False;

    # ***********************************************************

    def next(self):
        keyword = "";
        while (self.index < len(self.response)):
            letter = self.getTopLetter();
            if (self.isLetterSpecial(letter) or letter == "\""):
                ## when the last keyword not empty, handle last keyword first
                if (keyword != ""):
                    type = self.getType(keyword)
                    keyword = self.convertStrByType(keyword)
                    return Token(type=type, text=keyword);
                ## when the next keyword is string
                if (letter == "\""):
                    self.index += 1;
                    text = "";
                    while (self.getTopLetter() != "\""):
                        letter = self.getTopLetter()
                        text += letter;
                        self.index += 1;

                    self.index += 1;
                    return Token(type="str", text=text);
                ## when the top letter is space or break line, pleas jump
                if (letter == ' ' or letter == '\n'):
                    self.index += 1;
                    continue
                ## If letter is other puntuations, bracket, please return puntuations or bracket token
                type = self.getType(letter);
                self.index += 1;
                return Token(type=type, text=str(letter));
            # if not a special words, please continue recurrence and wait special letter
            keyword += letter;
            self.index += 1;
        return None;

    def getTokenLists(self):
        tokenLists = [];
        while (True):
            token = self.next();
            if (token == None):
                self.index = 0;
                return tokenLists;
            else:
                tokenLists.append(token);
        self.index = 0;

    def getMetaInfo(self, tokenList, start_index):
        infoLists = []
        index = start_index;
        assert tokenList[index] == "["
        queue_brackets = [];
        queue_brackets.append(tokenList[index].getText())
        index += 1;
        while (len(queue_brackets) != 0 and index < len(tokenList)):
            token = tokenList[index]
            if (self.getType(token) == 'bracket'):
                if (token.getText() in self.bracketsMap):
                    val = self.bracketsMap[token.getText()];
                    if (queue_brackets[-1] != val):
                        raise Exception("getMetaInfo: dataFormat is Wrong")
                    else:
                        queue_brackets.pop();
                else:
                    queue_brackets.append(tokenList[index].getText())
            elif ("name" == token):
                index += 2;
                infoLists.append(tokenList[index].getText())
                pass
            index += 1;
        return [infoLists, index];

    def readData(self, tokenList, start_index):
        assert isinstance(tokenList, list)
        # assert isinstance(tokenList[:], Token)
        infoLists = []
        index = start_index;
        assert tokenList[index] == "["
        queue_brackets = [];
        queue_brackets.append(tokenList[index].getText())
        index += 1;
        infoListItem = []
        while (len(queue_brackets) != 0 and index < len(tokenList)):

            token = tokenList[index]
            if (self.getType(token) == 'bracket'):
                if (token.getText() in self.bracketsMap):
                    val = self.bracketsMap[token.getText()];
                    if (queue_brackets[-1] != val):
                        raise Exception("getMetaInfo: dataFormat is Wrong")
                    else:
                        queue_brackets.pop();
                    infoLists.append(infoListItem)
                    infoListItem = [];
                else:
                    queue_brackets.append(tokenList[index].getText())
            elif (tokenList[index] != ","):
                # print(tokenList[index].text)
                infoListItem.append(tokenList[index].getText())
            index += 1;
        # return [infoLists, index];
        return [infoLists[:-1], index];

    def getInfoMap(self):
        tokenList = self.getTokenLists();
        i = 0;
        metaInfoList = []
        dataInfoList = []
        while (i < len(tokenList)):
            token = tokenList[i];
            if (token == "metadata"):
                [metaInfoList, index] = self.getMetaInfo(tokenList, i + 2)
                i = index;
                token = tokenList[i];
            elif (token == "data"):
                [dataInfoList, index] = self.readData(tokenList, i + 2)
                i = index;
                break;
            i += 1
        if (len(metaInfoList) == 0):
            raise Exception("getInfoMap: Error!! cannot get meta data correctly")

        if (len(dataInfoList) == 0):
            raise Exception("getInfoMap: Error!! cannot get dataInfoLists")
        for i in range(len(dataInfoList)):
            if (len(metaInfoList) != len(dataInfoList[i])):
                raise Exception("getInfoMap: Error1! metaInfoList lenght is not equal to ")

        InfoMap = {}
        for ele in metaInfoList:
            InfoMap[ele] = [];
        for ele in dataInfoList:
            for i in range(len(ele)):
                key = metaInfoList[i]
                InfoMap[key].append(ele[i])
        return InfoMap;

    # return (name, topNumber)
    def getTopDatas(self, InfoMap, key, num):
        key_lists = InfoMap[key]
        for ele in key_lists:
            assert isinstance(ele, float)
        test_lists = [];
        for i in range(len(key_lists)):
            test_lists.append((i, key_lists[i]))

        new_list = sorted(test_lists, key=lambda x: x[1], reverse=True)[:num]
        res = []
        name_list = InfoMap['name']
        for ele in new_list:
            val = ele[1];
            name = name_list[ele[0]]
            res.append((name, val))
            pass
        return {key: res};
        pass


def lambda_handler(event, context):
    # TODO implement
    client = boto3.client('ssm')
    document_name = 'arn:aws:ssm:us-west-2:077995606180:document/blue_toggle_newport_maintenance'
    parameters_NO = {
        'EnableMaintenanceMode': [
            'no',
        ]
    }

    parameters_Yes = {
        'EnableMaintenanceMode': [
            'yes',
        ]
    }

    t1 = RTViewTokenizer();
    InfoMap = t1.getInfoMap()
    res = t1.getTopDatas(InfoMap, "pendingMessageCount", 4)

    max_pendingMessageCount = 35000

    # tg = boto3.client('elbv2').describe_target_health(TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:077995606180:targetgroup/blue-newport-alb-tg/24a12db24c699a80')

    toggle_res = None
    if (res['pendingMessageCount'][0][1] > max_pendingMessageCount):
        client.start_automation_execution(DocumentName=document_name, Parameters=parameters_Yes)
        toggle_res = 'Yes'
    else:
        client.start_automation_execution(DocumentName=document_name, Parameters=parameters_NO)
        toggle_res = 'No'

    print("res: " + str(res))
    print("Toggle File Parameter: " + toggle_res)
    return {
        'statusCode': 200,
        # 'body': json.dumps('Hello from Lambda!'),
        'body': res
    }
