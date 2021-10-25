from model.yolo_loss import YOLOLoss
from yolo_utiles.plot import *
from model.model import *
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from yolo_utiles.dataloader import YoloDataset, yolo_dataset_collate
from yolo_utiles.early_stop import EarlyStopping
import os
from yolo import get_variable

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

epochs = 10
bs = 8
learning_rate = 0.001
num_workers = 2

train_annotation = 'train.txt'
test_annotation = 'test.txt'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
last_var_loss = [0, ]
avg_test_iou = []
weights_path, anchors_mask, input_shape, class_names, num_classes, anchors, num_anchors, confidence, nms_iou, letterbox_image = get_variable()


def fit(net, yolo_loss, opt, batch_data, batch_data_test):
    print("Train starts")
    trained_samples = 0
    all_samples = batch_data.dataset.__len__() * epochs
    test_iou = 0
    iter_ = 0
    for e in range(1, epochs + 1):
        loss = 0
        test_loss = 0
        # train start
        net.train()
        for iteration, (images, y) in enumerate(batch_data):

            images = torch.from_numpy(images).type(torch.FloatTensor).cuda()
            y = [torch.from_numpy(ann).type(torch.FloatTensor).cuda() for ann in y]
            opt.zero_grad(set_to_none=True)
            outputs = net(images)

            loss_value_all = 0
            num_pos_all = 0
            # loop will run three times for the three different size of anchor box
            for current_anchor in range(len(outputs)):
                loss_item, num_pos, iou = yolo_loss(current_anchor, outputs[current_anchor], y)
                loss_value_all += loss_item
                num_pos_all += num_pos
            loss_value = loss_value_all / num_pos_all

            trained_samples += images.shape[0]
            loss_value.backward()
            loss += loss_value.item()
            opt.step()


            if (iteration + 1) % 125 == 0:
                print('Epoch{}:[{}/{}({:.0f}%)]'.format(e, trained_samples, all_samples,
                                                        100 * trained_samples / all_samples))


        net.eval()
        for iteration, (images, y) in enumerate(batch_data_test):

            # prevent computational graph tracking
            with torch.no_grad():
                images = torch.from_numpy(images).type(torch.FloatTensor).cuda()
                y = [torch.from_numpy(i).type(torch.FloatTensor).cuda() for i in y]

                opt.zero_grad(set_to_none=True)
                outputs = net(images)
                loss_value_all = 0
                num_pos_all = 0
                # loop will run three times for the three different size of anchor box
                for current_anchor in range(len(outputs)):
                    loss_item, num_pos, iou = yolo_loss(current_anchor, outputs[current_anchor], y)
                    loss_value_all += loss_item
                    num_pos_all += num_pos
                loss_value = loss_value_all / num_pos_all
                test_loss += loss_value.item()
            test_iou += iou


            # Update the length of the progress each time

            iter_ += 1
        lr_scheduler.step()
        epoch_train_loss = round(loss / (num_train // bs), 5)
        epoch_test_loss = round(test_loss / (num_test // bs), 5)
        epoch_iou = (test_iou / iter_).item()
        avg_test_iou.append(epoch_iou)

        early_stop = EarlyStopping()
        early_stop = early_stop(test_loss)
        if early_stop and early_stop.counter == 3:
            print("Early stops")
            break
        if last_var_loss[0] > test_loss or e == 1:
            torch.save(model.state_dict(),
                       'results/epoch{}, training loss{},test_loss{}.pth'.format(
                           e + 1, epoch_train_loss, epoch_test_loss))
            print("Weights Saved")
        last_var_loss[0] = test_loss
        print()
        print('Train loss{}, Test loss{},Average{}'.format(epoch_train_loss, epoch_test_loss, epoch_iou))
        loss_list.append(epoch_train_loss)
        test_loss_list.append(epoch_test_loss)
        Plot_loss(loss_list, test_loss_list, avg_test_iou, epochs).plot()




def init_train(net, bs, lr, input_shape, train_lines, num_classes, val_lines, num_workers):
    torch.manual_seed(1)
    opt = optim.Adam(net.parameters(), lr)
    lr_scheduler = optim.lr_scheduler.ExponentialLR(opt, gamma=0.94)
    train_dataset = YoloDataset(train_lines, input_shape, num_classes, train=True)
    test_dataset = YoloDataset(val_lines, input_shape, num_classes, train=False)
    train = DataLoader(train_dataset, batch_size=bs, shuffle=True,
                       num_workers=num_workers, collate_fn=yolo_dataset_collate, drop_last=False, pin_memory=True)
    test = DataLoader(test_dataset, batch_size=bs, shuffle=True,
                      num_workers=num_workers, collate_fn=yolo_dataset_collate, drop_last=False, pin_memory=True)
    yolo_loss = YOLOLoss(anchors, num_classes, input_shape, anchors_mask)

    for param in net.darknet53.parameters():
        param.requires_grad = True
    return opt, lr_scheduler, yolo_loss, train_dataset, test_dataset, train, test


if __name__ == "__main__":
    loss_list = []
    test_loss_list = []

    if device:
        model = YoloBody(anchors_mask, num_classes).cuda()
    else:
        print("Do not have GPU")

    if weights_path != '':
        model.load_state_dict(torch.load(weights_path))

    with open(train_annotation, encoding="utf-8") as f:
        train_lines = f.readlines()
    with open(test_annotation, encoding="utf-8") as f:
        test_lines = f.readlines()

    num_train = len(train_lines)
    num_test = len(test_lines)

    if epochs > 0:
        opt, lr_scheduler, yolo_loss, train_dataset, test_dataset, train, test = init_train(model, bs,
                                                                                            learning_rate,
                                                                                            input_shape,
                                                                                            train_lines, num_classes,
                                                                                            test_lines,
                                                                                            num_workers)

        fit(model, yolo_loss, opt, train, test)


    plot = Plot_loss(loss_list, test_loss_list, avg_test_iou, epochs).plot()
