#main.py
from transformers import BertTokenizer
from transformers import BertForSequenceClassification
from transformers import BertConfig
from transformers import BertPreTrainedModel
import torch
import torch.nn as nn
from transformers import BertModel
import time
import argparse
from NewsData import NewsData
import os

def get_train_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--batch_size',type=int,default=10,help = '每批数据的数量')
    parser.add_argument('--nepoch',type=int,default=3,help = '训练的轮次')
    parser.add_argument('--lr',type=float,default=0.001,help = '学习率')
    parser.add_argument('--gpu',type=bool,default=True,help = '是否使用gpu')
    parser.add_argument('--num_workers',type=int,default=2,help='dataloader使用的线程数量')
    parser.add_argument('--num_labels',type=int,default=3,help='分类类数')
    parser.add_argument('--data_path',type=str,default='./data',help='数据路径')
    opt=parser.parse_args()
    print(opt)
    return opt

def get_model(opt):
    model = BertForSequenceClassification.from_pretrained('bert-base-chinese',num_labels=opt.num_labels)
    return model

def get_data(opt):
    trainset = NewsData(opt.data_path,is_train = 1)
    trainloader=torch.utils.data.DataLoader(trainset,batch_size=opt.batch_size,shuffle=True,num_workers=opt.num_workers)
    testset = NewsData(opt.data_path,is_train = 0)
    testloader=torch.utils.data.DataLoader(testset,batch_size=opt.batch_size,shuffle=False,num_workers=opt.num_workers)
    return trainloader,testloader



    
def train(epoch,model,trainloader,testloader,optimizer,opt):
    print('\ntrain-Epoch: %d' % (epoch+1))
    model.train()
    start_time = time.time()
    print_step = int(len(trainloader)/10)
    for batch_idx,(sue,label,posi) in enumerate(trainloader):
        if opt.gpu:
            sue = sue.cuda()
            posi = posi.cuda()
            label = label.unsqueeze(1).cuda()
        
        
        optimizer.zero_grad()
        outputs = model(sue, position_ids=posi,labels = label)

        loss, logits = outputs[0],outputs[1]
        loss.backward()
        optimizer.step()
        
        if batch_idx % print_step == 0:
            print("Epoch:%d [%d|%d] loss:%f" %(epoch+1,batch_idx,len(trainloader),loss.mean()))
    print("time:%.3f" % (time.time() - start_time))


def test(epoch,model,trainloader,testloader,opt):
    print('\ntest-Epoch: %d' % (epoch+1))
    model.eval()
    total=0
    correct=0
    with torch.no_grad():
        for batch_idx,(sue,label,posi) in enumerate(testloader):
            if opt.gpu:
                sue = sue.cuda()
                posi = posi.cuda()
                labels = label.unsqueeze(1).cuda()
                label = label.cuda()
            else:
                labels = label.unsqueeze(1)
            
            outputs = model(sue, labels=labels)
            loss, logits = outputs[:2]
            _,predicted=torch.max(logits.data,1)


            total+=sue.size(0)
            correct+=predicted.data.eq(label.data).cpu().sum()
    
    s = ("Acc:%.3f" %((1.0*correct.numpy())/total))
    print(s)


if __name__=='__main__':
        opt = get_train_args()
        model = get_model(opt)
        trainloader,testloader = get_data(opt)
        
        if opt.gpu:
            model.cuda()
        
        optimizer=torch.optim.SGD(model.parameters(),lr=opt.lr,momentum=0.9)
        
        if not os.path.exists('./model.pth'):
            for epoch in range(opt.nepoch):
                train(epoch,model,trainloader,testloader,optimizer,opt)
                test(epoch,model,trainloader,testloader,opt)
            torch.save(model.state_dict(),'./model.pth')
        else:
            model.load_state_dict(torch.load('model.pth'))
            print('模型存在,直接test')
            test(0,model,trainloader,testloader,opt)


       
