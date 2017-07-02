import argparse
import os
import time
import cv2
import numpy as np
import pandas as pd
from dataset import AmazonDataset
#from models import
from utils import AverageMeter
import torch
import torch.autograd as autograd
import torch.utils.data as data


parser = argparse.ArgumentParser(description='PyTorch Sealion count inference')
parser.add_argument('data', metavar='DIR',
                    help='path to dataset')
parser.add_argument('--model', default='countception', type=str, metavar='MODEL',
                    help='Name of model to train (default: "countception"')
parser.add_argument('--img-size', type=int, default=256, metavar='N',
                    help='Image patch size (default: 256)')
parser.add_argument('--batch-size', type=int, default=16, metavar='N',
                    help='input batch size for training (default: 16)')
parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')
parser.add_argument('--log-interval', type=int, default=100, metavar='N',
                    help='how many batches to wait before logging training status')
parser.add_argument('--num-processes', type=int, default=2, metavar='N',
                    help='how many training processes to use (default: 2)')
parser.add_argument('-r', '--restore-checkpoint', default=None,
                    help='path to restore checkpoint, e.g. ./checkpoint-1.tar')
parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')
parser.add_argument('--num-gpu', type=int, default=1,
                    help='Number of GPUS to use')

COLS = ['test_id', 'adult_males', 'subadult_males', 'adult_females', 'juveniles', 'pups']


def main():
    args = parser.parse_args()

    batch_size = args.batch_size
    img_size = (args.img_size, args.img_size)

    debug_image = False
    debug_model = False
    num_outputs = 4
    dataset = AmazonDataset(
        args.data,
        train=False,
        img_size=img_size,
        per_image_norm=True)

    loader = data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=args.num_processes)

    if args.model == 'cnet':
        model = ModelCnet(
            outplanes=num_outputs, target_size=patch_size, debug=debug_model)
    elif args.model == 'countception' or args.model == 'cc':
        model = ModelCountception(
            outplanes=num_outputs, use_logits=use_logits, logits_per_output=num_logits, debug=debug_model)
    else:
        assert False and "Invalid model"

    if not args.no_cuda:
        if args.num_gpu > 1:
            model = torch.nn.DataParallel(model, device_ids=list(range(args.num_gpu))).cuda()
        else:
            model.cuda()

    if args.restore_checkpoint is not None:
        assert os.path.isfile(args.restore_checkpoint), '%s not found' % args.restore_checkpoint
        checkpoint = torch.load(args.restore_checkpoint)
        model.load_state_dict(checkpoint['state_dict'])
        print('Model restored from file: %s' % args.restore_checkpoint)

    model.eval()

    batch_time_m = AverageMeter()
    data_time_m = AverageMeter()
    results = []
    try:
        end = time.time()
        for batch_idx, (input, target, index) in enumerate(loader):
            data_time_m.update(time.time() - end)
            if not args.no_cuda:
                input_var, target_var = autograd.Variable(input.cuda()), autograd.Variable(target.cuda())
            else:
                input_var, target_var = autograd.Variable(input), autograd.Variable(target)
            output = model(input_var)
            output = output.permute(0, 2, 3, 1)
            output = output.cpu().data.numpy()

            for result_index, o in zip(index, output):
                input_id, index, patch_index = result_index
                #print('input_id, indexx
                # end iterating through batch

            batch_time_m.update(time.time() - end)
            if batch_idx % args.log_interval == 0:
                print('Inference: [{}/{} ({:.0f}%)]  '
                      'Time: {batch_time.val:.3f}s, {rate:.3f}/s  '
                      '({batch_time.avg:.3f}s, {rate_avg:.3f}/s)  '
                      'Data: {data_time.val:.3f} ({data_time.avg:.3f})'.format(
                    batch_idx * len(input), len(loader.sampler),
                    100. * batch_idx / len(loader),
                    batch_time=batch_time_m,
                    rate=input_var.size(0) / batch_time_m.val,
                    rate_avg=input_var.size(0) / batch_time_m.avg,
                    data_time=data_time_m))

            end = time.time()
            #end iterating through dataset
    except KeyboardInterrupt:
        pass
    results_df = pd.DataFrame(results, columns=COLS)
    results_df.to_csv('submission.csv', index=False)


if __name__ == '__main__':
    main()